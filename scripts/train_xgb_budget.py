"""
Eleos Feasibility System - XGBoost Regression Model
Objective: Predict realistic expected project budget (expected_budget_inr)
for new NGO proposals based on project scope and NGO operational track record.

Features:
- Primary/Secondary Sectors (multi-label parsing for secondary_sectors)
- Geographical location (state, district, remote area flag)
- Disaster relief flag
- Project scope (duration, beneficiaries, villages, milestones)
- NGO track record (age, operational footprint, prior project history)
- Engineered interaction and scale ratios

Validation:
- Chronological Split:
  Train: 2018-2022 (Historical baseline + pre-2023)
  Validation: 2023 (Early stopping & hyperparameter tuning)
  Test: 2024-2025 (Unseen future performance)
"""

import os
import json
import ast
import pickle
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb


# Canonical list of secondary sectors encountered in the ecosystem
ALL_SECTORS = [
    "Education & Skill Development",
    "Emergency Relief & Rehabilitation",
    "Healthcare & Nutrition",
    "Social Welfare & Community Development",
    "Water, Sanitation & Environment"
]


class EleosFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Transforms raw NGO project proposal features:
    1. Imputes prior_max_beneficiaries (0 for no history)
    2. Constructs domain interaction and scale ratio features:
       - has_prior_projects: prior_projects_count > 0
       - remote_disaster_interaction: is_remote_area * is_disaster_relief
       - beneficiary_density: beneficiaries_reported / villages_covered (safe div)
       - project_scale_vs_ngo_history: beneficiaries_reported / max(prior_max_beneficiaries, 1)
       - beneficiaries_per_prior_project: beneficiaries_reported / max(prior_projects_count, 1)
    3. Multi-label parses secondary_sectors JSON string into binary indicators
    """
    def __init__(self, known_sectors=None):
        self.known_sectors = known_sectors if known_sectors is not None else ALL_SECTORS

    def fit(self, X, y=None):
        return self

    def _parse_secondary(self, val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return []
        if isinstance(val, (list, set, tuple)):
            return list(val)
        if isinstance(val, str):
            val_clean = val.strip()
            if not val_clean:
                return []
            try:
                return json.loads(val_clean)
            except Exception:
                try:
                    return ast.literal_eval(val_clean)
                except Exception:
                    return [s.strip() for s in val_clean.replace("[", "").replace("]", "").replace("'", "").replace('"', '').split(",") if s.strip()]
        return []

    def transform(self, X):
        df = X.copy()
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        # 1. Defensively impute numeric and scale features
        for num_col in [
            "prior_max_beneficiaries", "prior_projects_count", "beneficiaries_reported",
            "villages_covered", "duration_months", "milestones_reported",
            "ngo_age_years_at_start", "number_of_operational_states",
            "number_of_operational_districts", "number_of_sectors"
        ]:
            if num_col not in df.columns:
                df[num_col] = 0.0
            else:
                df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0.0)

        # Convert booleans
        for b_col in ["is_remote_area", "is_disaster_relief"]:
            if b_col not in df.columns:
                df[b_col] = 0.0
            else:
                df[b_col] = df[b_col].astype(str).str.lower().isin(["true", "1", "yes"]).astype(float)
        is_remote = df["is_remote_area"]
        is_disaster = df["is_disaster_relief"]

        # 2. Engineered features
        # has_prior_projects: distinguishes NGOs with no history cleanly
        df["has_prior_projects"] = (df["prior_projects_count"] > 0).astype(float)

        # remote_disaster_interaction: compounding logistics / emergency premium
        df["remote_disaster_interaction"] = (is_remote * is_disaster).astype(float)

        # beneficiary_density: beneficiaries per village covered (safe div)
        df["beneficiary_density"] = np.where(
            df["villages_covered"] > 0,
            df["beneficiaries_reported"] / df["villages_covered"],
            0.0
        )

        # project_scale_vs_ngo_history: project beneficiaries vs max prior beneficiaries
        df["project_scale_vs_ngo_history"] = (
            df["beneficiaries_reported"] / np.maximum(df["prior_max_beneficiaries"], 1.0)
        )

        # beneficiaries_per_prior_project: project beneficiaries vs prior projects count
        df["beneficiaries_per_prior_project"] = (
            df["beneficiaries_reported"] / np.maximum(df["prior_projects_count"], 1.0)
        )

        # 3. Multi-label parse secondary_sectors into individual binary indicator columns
        raw_sec = df["secondary_sectors"] if "secondary_sectors" in df.columns else pd.Series([[]] * len(df))
        parsed_sec = raw_sec.apply(self._parse_secondary)
        for sec in self.known_sectors:
            col_name = f"sec_sector_{sec.lower().replace(' ', '_').replace('&', 'and')}"
            df[col_name] = parsed_sec.apply(lambda lst: 1.0 if sec in lst else 0.0)

        # Drop the original secondary_sectors string column so ColumnTransformer deals with clean tabular data
        df = df.drop(columns=["secondary_sectors"], errors="ignore")
        return df


class EleosBudgetPredictor(BaseEstimator):
    """
    Unified end-to-end inference wrapper:
    - Encapsulates feature engineering, one-hot encoding, and trained XGBoost model
    - Enforces non-negative, plausible budget predictions
    """
    def __init__(self, preprocessor, model, feature_names=None):
        self.preprocessor = preprocessor
        self.model = model
        self.feature_names = feature_names

    def predict(self, X):
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, list):
            X = pd.DataFrame(X)
        X_trans = self.preprocessor.transform(X)
        preds = self.model.predict(X_trans)
        # Ensure predicted budgets are strictly positive and plausible
        return np.maximum(preds, 10000.0)


def build_preprocessor():
    categorical_cols = [
        "primary_sector",
        "location_state_primary",
        "location_district_primary"
    ]
    numeric_and_binary_cols = [
        "is_remote_area",
        "is_disaster_relief",
        "duration_months",
        "beneficiaries_reported",
        "villages_covered",
        "milestones_reported",
        "ngo_age_years_at_start",
        "number_of_operational_states",
        "number_of_operational_districts",
        "number_of_sectors",
        "prior_projects_count",
        "prior_max_beneficiaries",
        "has_prior_projects",
        "remote_disaster_interaction",
        "beneficiary_density",
        "project_scale_vs_ngo_history",
        "beneficiaries_per_prior_project"
    ] + [f"sec_sector_{sec.lower().replace(' ', '_').replace('&', 'and')}" for sec in ALL_SECTORS]

    col_transformer = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
            ("num", "passthrough", numeric_and_binary_cols)
        ],
        remainder="drop"
    )

    full_preprocessor = Pipeline([
        ("feature_engineer", EleosFeatureEngineer(known_sectors=ALL_SECTORS)),
        ("column_transformer", col_transformer)
    ])
    return full_preprocessor


def get_feature_names(preprocessor):
    col_tf = preprocessor.named_steps["column_transformer"]
    cat_tf = col_tf.named_transformers_["cat"]
    cat_names = cat_tf.get_feature_names_out().tolist()
    num_names = col_tf.transformers[1][2]
    return cat_names + list(num_names)


def evaluate_set(name, y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"\n[{name} Set Performance]")
    print(f"  MAE  : INR {mae:,.2f}")
    print(f"  RMSE : INR {rmse:,.2f}")
    print(f"  R^2  : {r2:.4f}")
    return {"MAE": mae, "RMSE": rmse, "R2": r2}


def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(curr_dir)
    data_dir = os.path.join(base_dir, "feasibility_data")
    models_dir = os.path.join(base_dir, "models")
    outputs_dir = os.path.join(base_dir, "outputs")

    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)

    features_path = os.path.join(data_dir, "feasibility_features.csv") if os.path.exists(os.path.join(data_dir, "feasibility_features.csv")) else os.path.join(data_dir, "feasibility_features (1).csv")
    targets_path = os.path.join(data_dir, "feasibility_targets.csv") if os.path.exists(os.path.join(data_dir, "feasibility_targets.csv")) else os.path.join(data_dir, "feasibility_targets (1).csv")

    print(f"Loading data from {data_dir}...")
    feat_df = pd.read_csv(features_path)
    targ_df = pd.read_csv(targets_path)

    # Merge on project_id
    df = pd.merge(feat_df, targ_df, on="project_id", how="inner")
    print(f"Total merged records: {len(df)}")

    # Sort strictly chronologically by start_date to prevent temporal leakage
    df["start_date_dt"] = pd.to_datetime(df["start_date"])
    df = df.sort_values(by=["start_date_dt", "project_id"]).reset_index(drop=True)
    df["start_year"] = df["start_date_dt"].dt.year

    # Optimal Chronological Split: 70% Train, 15% Validation, 15% Test
    total_n = len(df)
    n_train = int(total_n * 0.70)
    n_val = int(total_n * 0.15)
    n_test = total_n - n_train - n_val

    train_df = df.iloc[:n_train].copy()
    val_df = df.iloc[n_train:n_train + n_val].copy()
    test_df = df.iloc[n_train + n_val:].copy()

    print(f"\nChronological Split Breakdown (70% Train / 15% Val / 15% Test):")
    print(f"  Training Set   (70%, {train_df['start_date'].min()} to {train_df['start_date'].max()}): {len(train_df)} projects")
    print(f"  Validation Set (15%, {val_df['start_date'].min()} to {val_df['start_date'].max()}): {len(val_df)} projects")
    print(f"  Test Set       (15%, {test_df['start_date'].min()} to {test_df['start_date'].max()}): {len(test_df)} projects")

    # Select features
    feature_cols = [
        "primary_sector",
        "secondary_sectors",
        "location_state_primary",
        "location_district_primary",
        "is_remote_area",
        "is_disaster_relief",
        "duration_months",
        "beneficiaries_reported",
        "villages_covered",
        "milestones_reported",
        "ngo_age_years_at_start",
        "number_of_operational_states",
        "number_of_operational_districts",
        "number_of_sectors",
        "prior_projects_count",
        "prior_max_beneficiaries"
    ]

    target_col = "expected_budget_inr"

    X_train_raw = train_df[feature_cols]
    y_train = train_df[target_col].values

    X_val_raw = val_df[feature_cols]
    y_val = val_df[target_col].values

    X_test_raw = test_df[feature_cols]
    y_test = test_df[target_col].values

    # Preprocessing Pipeline
    preprocessor = build_preprocessor()
    print("\nFitting feature engineering and categorical encoding pipeline on training data...")
    X_train_trans = preprocessor.fit_transform(X_train_raw)
    X_val_trans = preprocessor.transform(X_val_raw)
    X_test_trans = preprocessor.transform(X_test_raw)

    feature_names = get_feature_names(preprocessor)
    print(f"Total encoded features: {len(feature_names)}")

    # Model Configuration as specified:
    # n_estimators=500, learning_rate=0.05, max_depth=4, min_child_weight=3,
    # subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0,
    # objective="reg:squarederror", random_state=42
    model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=4,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="reg:squarederror",
        random_state=42,
        early_stopping_rounds=30,
        eval_metric="rmse"
    )

    print("\nTraining XGBoost Regressor with early stopping on 2023 validation set...")
    model.fit(
        X_train_trans,
        y_train,
        eval_set=[(X_train_trans, y_train), (X_val_trans, y_val)],
        verbose=50
    )

    print(f"\nBest iteration: {model.best_iteration}")

    # Predictions
    y_train_pred = np.maximum(model.predict(X_train_trans), 10000.0)
    y_val_pred = np.maximum(model.predict(X_val_trans), 10000.0)
    y_test_pred = np.maximum(model.predict(X_test_trans), 10000.0)

    # Evaluate
    train_metrics = evaluate_set("Train (2018-2022)", y_train, y_train_pred)
    val_metrics = evaluate_set("Validation (2023)", y_val, y_val_pred)
    test_metrics = evaluate_set("Test (2024-2025)", y_test, y_test_pred)

    # Overfitting Check
    r2_train = train_metrics["R2"]
    r2_test = test_metrics["R2"]
    r2_gap = r2_train - r2_test
    print(f"\nOverfitting Diagnostics:")
    print(f"  Train R^2: {r2_train:.4f} | Test R^2: {r2_test:.4f} | Gap: {r2_gap:.4f}")
    if r2_gap < 0.15:
        print("  Status: EXCELLENT generalization (Train-Test R^2 gap < 0.15). No severe overfitting.")
    elif r2_gap < 0.25:
        print("  Status: ACCEPTABLE generalization (Train-Test R^2 gap < 0.25).")
    else:
        print("  Status: WARNING - Model may be exhibiting overfitting.")

    # Packaging complete end-to-end pipeline
    full_pipeline = EleosBudgetPredictor(
        preprocessor=preprocessor,
        model=model,
        feature_names=feature_names
    )

    pipeline_path = os.path.join(models_dir, "xgb_budget_pipeline.pkl")
    with open(pipeline_path, "wb") as f:
        pickle.dump(full_pipeline, f)
    print(f"\nSaved complete pipeline to: {pipeline_path}")

    # Feature Importance
    importance_dict = model.get_booster().get_score(importance_type="gain")
    # Match feature names
    feat_importances = []
    for idx, f_name in enumerate(feature_names):
        f_key = f"f{idx}"
        gain = importance_dict.get(f_key, 0.0)
        feat_importances.append({"feature": f_name, "gain_importance": gain})

    fi_df = pd.DataFrame(feat_importances)
    total_gain = fi_df["gain_importance"].sum()
    fi_df["relative_importance_pct"] = (fi_df["gain_importance"] / total_gain * 100) if total_gain > 0 else 0.0
    fi_df = fi_df.sort_values(by="gain_importance", ascending=False).reset_index(drop=True)

    fi_path = os.path.join(outputs_dir, "feature_importance.csv")
    fi_df.to_csv(fi_path, index=False)
    print(f"Saved feature importances to: {fi_path}")

    print("\nTop 10 Most Important Features:")
    for i, row in fi_df.head(10).iterrows():
        print(f"  {i+1:2d}. {row['feature']:<35} (Gain: {row['gain_importance']:,.1f} | {row['relative_importance_pct']:.2f}%)")

    # Generate full predictions.csv
    print("\nGenerating predictions.csv across entire dataset...")
    X_all_trans = preprocessor.transform(df[feature_cols])
    df["predicted_expected_budget_inr"] = np.maximum(model.predict(X_all_trans), 10000.0)
    df["actual expected_budget_inr"] = df["expected_budget_inr"]
    df["actual_expected_budget_inr"] = df["expected_budget_inr"]
    df["prediction_error"] = df["predicted_expected_budget_inr"] - df["actual expected_budget_inr"]
    df["prediction_error_percentage"] = (df["prediction_error"] / df["actual expected_budget_inr"]) * 100.0

    predictions_df = df[[
        "project_id",
        "start_year",
        "actual expected_budget_inr",
        "actual_expected_budget_inr",
        "predicted_expected_budget_inr",
        "prediction_error",
        "prediction_error_percentage"
    ]].copy()

    # Tag split group for clarity (70% Train, 15% Val, 15% Test)
    split_tags = ["train"] * n_train + ["validation"] * n_val + ["test"] * n_test
    predictions_df["split_group"] = split_tags

    preds_path = os.path.join(outputs_dir, "predictions.csv")
    predictions_df.to_csv(preds_path, index=False, float_format="%.2f")
    print(f"Saved predictions to: {preds_path}")

    # Save summary report JSON
    summary_report = {
        "model": "XGBoost Regressor (Eleos Feasibility)",
        "split_chronology": {
            "train": f"{train_df['start_date'].min()} to {train_df['start_date'].max()} (70%)",
            "val": f"{val_df['start_date'].min()} to {val_df['start_date'].max()} (15%)",
            "test": f"{test_df['start_date'].min()} to {test_df['start_date'].max()} (15%)"
        },
        "sample_counts": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
            "total": len(df)
        },
        "metrics": {
            "train": train_metrics,
            "validation": val_metrics,
            "test": test_metrics
        },
        "overfitting_diagnostics": {
            "r2_train": r2_train,
            "r2_test": r2_test,
            "r2_gap": r2_gap,
            "overfitting_observed": bool(r2_gap > 0.25)
        },
        "top_features": fi_df.head(10).to_dict(orient="records")
    }

    report_path = os.path.join(outputs_dir, "feasibility_model_report.json")
    with open(report_path, "w") as f:
        json.dump(summary_report, f, indent=2)
    print(f"Saved feasibility model report to: {report_path}")


if __name__ == "__main__":
    main()
