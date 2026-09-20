"""
ELEOS — Member 1: Unsupervised Financial Anomaly Detection
Uses sklearn.ensemble.IsolationForest to detect statistically unusual financial profiles.

IMPORTANT METHODOLOGICAL PRINCIPLE:
Isolation Forest detects statistical unusualness relative to the reference population.
It does NOT detect fraud, criminal behavior, or moral character.
An unusual financial structure (e.g. high cash buffer during a capital campaign) can be fully legitimate.

Configurable parameters:
- contamination: default 0.05 (justified as capturing the 5% distribution tail of atypical profiles in non-profit distributions)
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "synthetic"
DATA_DIR = ROOT_DIR / "data" / "reference"
OUTPUTS_DIR = ROOT_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR = ROOT_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONTAMINATION = 0.05
RANDOM_SEED = 42

FINANCIAL_FEATURE_COLS = [
    "log_income",
    "log_expenditure",
    "programme_expense_ratio",
    "administrative_expense_ratio",
    "fundraising_expense_ratio",
    "surplus_margin",
    "cash_to_expense_ratio",
    "grant_dependency_ratio",
    "financial_missingness_ratio"
]


def prepare_anomaly_feature_matrix(df_fin_feats: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Prepares and transforms numerical financial features for Isolation Forest.
    Applies log1p transformation to monetary values and medians imputation.
    """
    df = df_fin_feats.copy()

    # Log transformations for heavily right-skewed monetary amounts
    df["log_income"] = np.log1p(df["total_income"].fillna(0).clip(lower=0))
    df["log_expenditure"] = np.log1p(df["total_expenditure"].fillna(0).clip(lower=0))

    X = df[FINANCIAL_FEATURE_COLS].copy()

    # Compute training-set median statistics for imputation (preserving reference distribution)
    imputation_medians = {}
    for col in FINANCIAL_FEATURE_COLS:
        med_val = float(X[col].median(skipna=True))
        if np.isnan(med_val):
            med_val = 0.0
        imputation_medians[col] = med_val
        X[col] = X[col].fillna(med_val)

    return X, imputation_medians


def train_anomaly_detector(
    df_fin_feats: pd.DataFrame,
    contamination: float = DEFAULT_CONTAMINATION,
    random_state: int = RANDOM_SEED
) -> Tuple[IsolationForest, pd.DataFrame, Dict[str, Any]]:
    """
    Trains unsupervised Isolation Forest on reference population financial features.
    """
    X, imputation_medians = prepare_anomaly_feature_matrix(df_fin_feats)

    # Train Isolation Forest
    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X)

    # Compute raw decision function anomaly scores (lower = more abnormal)
    # scikit-learn convention: negative scores are outliers, positive are inliers
    raw_scores = model.decision_function(X)
    preds = model.predict(X)  # 1 for inlier, -1 for outlier

    df_results = df_fin_feats.copy()
    df_results["financial_anomaly_score"] = np.round(raw_scores, 4)

    # Percentile-based categorization for explainability
    # Outlier: bottom contamination fraction (e.g. lowest 5%)
    # Borderline: next 10% lowest
    # Normal: upper 85%
    p_outlier = np.percentile(raw_scores, contamination * 100)
    p_borderline = np.percentile(raw_scores, (contamination + 0.10) * 100)

    labels = []
    for s in raw_scores:
        if s <= p_outlier:
            labels.append("Outlier")
        elif s <= p_borderline:
            labels.append("Borderline")
        else:
            labels.append("Normal")

    df_results["financial_anomaly_label"] = labels

    outlier_cnt = labels.count("Outlier")
    borderline_cnt = labels.count("Borderline")
    normal_cnt = labels.count("Normal")

    metadata = {
        "model_name": "IsolationForest",
        "model_version": "iforest-v1.0",
        "feature_columns": FINANCIAL_FEATURE_COLS,
        "contamination": contamination,
        "contamination_justification": f"Contamination is set to {contamination:.2f} to reflect expected structural variance across non-profit business models without alleging moral wrongdoing.",
        "training_population_size": len(df_fin_feats),
        "random_seed": random_state,
        "imputation_medians": imputation_medians,
        "percentile_thresholds": {
            "outlier_cutoff_score": round(float(p_outlier), 4),
            "borderline_cutoff_score": round(float(p_borderline), 4)
        },
        "distribution_summary": {
            "normal_count": normal_cnt,
            "borderline_count": borderline_cnt,
            "outlier_count": outlier_cnt,
            "outlier_percentage": round(outlier_cnt / len(df_fin_feats) * 100, 2)
        }
    }

    # Persist model artifact and metadata
    joblib.dump(model, MODELS_DIR / "isolation_forest.pkl")
    with open(OUTPUTS_DIR / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return model, df_results, metadata


def run_anomaly_detection(contamination: float = DEFAULT_CONTAMINATION) -> pd.DataFrame:
    print(f"[4/7] Running Isolation Forest anomaly detection (contamination={contamination})...")

    feats_path = DATA_DIR / "financial_features.csv"
    if not feats_path.exists():
        raise FileNotFoundError(f"Missing {feats_path}. Run feature_engineering.py first.")

    df_fin_feats = pd.read_csv(feats_path)
    model, df_scored, meta = train_anomaly_detector(df_fin_feats, contamination=contamination)

    # Save updated financial features with anomaly scores
    df_scored.to_csv(DATA_DIR / "financial_features.csv", index=False)

    print(f"  [SUCCESS] Anomaly detection complete. Normal: {meta['distribution_summary']['normal_count']}, "
          f"Borderline: {meta['distribution_summary']['borderline_count']}, "
          f"Outliers: {meta['distribution_summary']['outlier_count']}")
    return df_scored


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Isolation Forest for financial anomaly detection")
    parser.add_argument("--contamination", type=float, default=DEFAULT_CONTAMINATION, help="Configurable contamination parameter")
    args = parser.parse_args()

    run_anomaly_detection(contamination=args.contamination)

