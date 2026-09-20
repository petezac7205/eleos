"""
Eleos Feasibility System - Final Feasibility Scoring Module
Integrates the existing XGBoost regression pipeline to evaluate end-to-end
project feasibility across four deterministic pillars:

FS = 0.40 * B + 0.25 * S + 0.20 * C + 0.15 * I

All component scores are strictly 0–100.
Labels (DB-compatible lowercase):
  90–100 : high (Very High feasibility)
  75–89  : high
  60–74  : moderate
  40–59  : low
  0–39   : very_low
"""

import os
import pickle
import __main__
import numpy as np
import pandas as pd

# Import the existing feature engineering classes for pipeline compatibility
from train_xgb_budget import EleosFeatureEngineer, EleosBudgetPredictor, ALL_SECTORS

# Register in __main__ so pickle can unpickle from any caller script
setattr(__main__, "EleosFeatureEngineer", EleosFeatureEngineer)
setattr(__main__, "EleosBudgetPredictor", EleosBudgetPredictor)


class FeasibilityScorer:
    """
    Computes the complete Eleos Feasibility Score (FS):
    - B: Budget Realism (40%) - anchored to XGBoost predicted expected budget
    - S: Project Scale (25%) - scope, density, and scale vs historical track record
    - C: Cost Context (20%) - external benchmarks (default 65 when unavailable)
    - I: Implementation Capacity (15%) - NGO track record (neutral for first-time NGOs)
    """

    def __init__(self, model_path=None, benchmarks_path=None):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(curr_dir)
        if model_path is None:
            model_path = os.path.join(base_dir, "models", "xgb_budget_pipeline.pkl")
            if not os.path.exists(model_path):
                model_path = os.path.join(curr_dir, "xgb_budget_pipeline.pkl")
        self.model_path = model_path
        self._load_pipeline()

        if benchmarks_path is None:
            benchmarks_path = os.path.join(base_dir, "feasibility_data", "commodity_benchmarks.csv")
            if not os.path.exists(benchmarks_path):
                benchmarks_path = os.path.join(curr_dir, "commodity_benchmarks.csv")
        self.benchmarks_path = benchmarks_path
        self._load_benchmarks()

    def _load_benchmarks(self):
        self.benchmarks_df = None
        self.national_benchmarks = None
        if self.benchmarks_path and os.path.exists(self.benchmarks_path):
            try:
                df = pd.read_csv(self.benchmarks_path)
                df["state_lower"] = df["state"].astype(str).str.strip().str.lower()
                self.benchmarks_df = df.set_index("state_lower")
                num_cols = [c for c in df.columns if c not in ["state", "state_lower"]]
                self.national_benchmarks = df[num_cols].mean().to_dict()
            except Exception as e:
                print(f"Warning: Could not load benchmarks from {self.benchmarks_path}: {e}")

    def _load_pipeline(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model pipeline not found at: {self.model_path}")
        with open(self.model_path, "rb") as f:
            self.pipeline = pickle.load(f)

    @staticmethod
    def _interpolate_budget_realism(deviation_pct):
        """
        Anchors:
          0–15% -> 100
          20%   -> 90
          30%   -> 70
          40%   -> 50
          50%   -> 25
          >50%  -> progressively lower (linear down to 0 at 100%+)
        """
        dev = max(0.0, float(deviation_pct))
        if dev <= 15.0:
            return 100.0
        elif dev <= 20.0:
            # 15% -> 100, 20% -> 90
            return 100.0 - (dev - 15.0) * (10.0 / 5.0)
        elif dev <= 30.0:
            # 20% -> 90, 30% -> 70
            return 90.0 - (dev - 20.0) * (20.0 / 10.0)
        elif dev <= 40.0:
            # 30% -> 70, 40% -> 50
            return 70.0 - (dev - 30.0) * (20.0 / 10.0)
        elif dev <= 50.0:
            # 40% -> 50, 50% -> 25
            return 50.0 - (dev - 40.0) * (25.0 / 10.0)
        else:
            # >50%: 25 at 50% down to 0 at 100%
            return max(0.0, 25.0 - (dev - 50.0) * 0.5)

    def calculate_budget_realism(self, submitted_budget, predicted_expected_budget, line_items=None):
        """
        Component B (40%): Evaluates submitted budget vs XGBoost predicted expected budget.
        Incorporates line-item admin and contingency checks if line items are provided.
        """
        if predicted_expected_budget <= 0:
            return 50.0, "Predicted budget invalid; default neutral score applied."

        deviation_pct = (abs(submitted_budget - predicted_expected_budget) / predicted_expected_budget) * 100.0
        macro_score = self._interpolate_budget_realism(deviation_pct)

        line_item_explanations = []
        line_item_penalty = 0.0

        if line_items is not None and len(line_items) > 0:
            items_df = pd.DataFrame(line_items) if not isinstance(line_items, pd.DataFrame) else line_items
            if "total_cost_inr" in items_df.columns and "category" in items_df.columns:
                total_line_cost = items_df["total_cost_inr"].sum()
                if total_line_cost > 0:
                    admin_cost = items_df[items_df["category"].str.lower() == "admin"]["total_cost_inr"].sum()
                    contingency_cost = items_df[items_df["category"].str.lower() == "contingency"]["total_cost_inr"].sum()

                    admin_pct = (admin_cost / total_line_cost) * 100.0
                    cont_pct = (contingency_cost / total_line_cost) * 100.0

                    # Standard CSR/FCRA benchmark: Admin expenses ideally <= 20%
                    if admin_pct > 25.0:
                        penalty = min(15.0, (admin_pct - 20.0) * 1.0)
                        line_item_penalty += penalty
                        line_item_explanations.append(f"High admin overhead ({admin_pct:.1f}% vs 20% FCRA threshold)")

                    # Contingency ideally <= 15%
                    if cont_pct > 20.0:
                        penalty = min(10.0, (cont_pct - 15.0) * 0.8)
                        line_item_penalty += penalty
                        line_item_explanations.append(f"Elevated contingency allocation ({cont_pct:.1f}% vs 15% benchmark)")

        final_b = max(0.0, min(100.0, macro_score - line_item_penalty))

        dev_dir = "higher" if submitted_budget > predicted_expected_budget else "lower"
        explanation = f"Submitted budget is {deviation_pct:.1f}% {dev_dir} than predicted expected budget (INR {predicted_expected_budget:,.2f})."
        if line_item_explanations:
            explanation += f" Line-item notes: {'; '.join(line_item_explanations)}."
        else:
            explanation += " Overall budget aligns within acceptable tolerance band." if deviation_pct <= 20 else ""

        return final_b, explanation

    def calculate_project_scale(self, project_data):
        """
        Component S (25%): Evaluates whether the proposed project's size, scope,
        and geographic footprint are structurally reasonable.
        Reuses exact existing definition: project_scale_vs_ngo_history = beneficiaries / max(prior_max_beneficiaries, 1).
        """
        beneficiaries = float(project_data.get("beneficiaries_reported", 0))
        villages = float(project_data.get("villages_covered", 1))
        duration_months = max(1.0, float(project_data.get("duration_months", 12)))
        operational_states = max(1.0, float(project_data.get("number_of_operational_states", 1)))
        operational_districts = max(1.0, float(project_data.get("number_of_operational_districts", 1)))
        prior_max_ben = float(project_data.get("prior_max_beneficiaries", 0) or 0)
        has_prior = int(project_data.get("prior_projects_count", 0) > 0)

        # 1. Beneficiary Density Check (beneficiaries per village)
        density = beneficiaries / max(villages, 1.0)
        density_score = 100.0
        if density > 1500.0:
            density_score -= min(35.0, (density - 1500.0) / 100.0 * 2.0)
        elif density < 10.0 and beneficiaries > 200:
            density_score -= 15.0  # extreme dilution across villages

        # 2. Operational Pace (beneficiaries per month)
        monthly_pace = beneficiaries / duration_months
        pace_score = 100.0
        if monthly_pace > 1500.0:
            pace_score -= min(30.0, (monthly_pace - 1500.0) / 100.0 * 1.5)

        # 3. Project Duration Feasibility
        duration_score = 100.0
        if duration_months < 4 and beneficiaries > 2000:
            duration_score -= 30.0  # highly compressed timeframe
        elif duration_months > 36:
            duration_score -= 10.0  # multi-year planning risk

        # 4. Project Scale vs NGO Track Record (Exact existing definition)
        project_scale_vs_ngo_history = beneficiaries / max(prior_max_ben, 1.0)
        history_scale_score = 100.0
        scale_notes = []

        if has_prior:
            # Established NGO: compare current project to historical max
            if project_scale_vs_ngo_history <= 2.5:
                history_scale_score = 100.0
                scale_notes.append(f"Scale expansion ({project_scale_vs_ngo_history:.1f}x prior max) is well within organic growth capacity")
            elif project_scale_vs_ngo_history <= 5.0:
                history_scale_score = 80.0
                scale_notes.append(f"Moderate scale jump ({project_scale_vs_ngo_history:.1f}x prior max)")
            else:
                history_scale_score = max(40.0, 80.0 - (project_scale_vs_ngo_history - 5.0) * 3.0)
                scale_notes.append(f"Substantial scale expansion ({project_scale_vs_ngo_history:.1f}x prior max) poses execution strain")
        else:
            # First-time NGO: evaluate absolute scale reasonableness for a new entity
            if beneficiaries <= 2500:
                history_scale_score = 90.0
                scale_notes.append(f"Initial project scale ({beneficiaries:,.0f} beneficiaries) is appropriate for a first-time proposal")
            elif beneficiaries <= 5000:
                history_scale_score = 75.0
                scale_notes.append(f"Relatively ambitious first-time scale ({beneficiaries:,.0f} beneficiaries)")
            else:
                history_scale_score = 55.0
                scale_notes.append(f"High-volume beneficiary target ({beneficiaries:,.0f}) for an organization with no prior documented projects")

        # Blend sub-dimensions into S (Scale)
        s_score = (
            0.35 * history_scale_score +
            0.25 * density_score +
            0.25 * pace_score +
            0.15 * duration_score
        )
        s_score = max(0.0, min(100.0, s_score))

        explanation = f"Scale index {s_score:.1f}/100 based on {beneficiaries:,.0f} beneficiaries across {villages:.0f} villages ({density:.1f} per village) over {duration_months:.0f} months. {'; '.join(scale_notes)}."
        return s_score, explanation

    def calculate_cost_context(self, project_data=None, line_items=None, external_benchmarks=None):
        """
        Component C (20%): Evaluates external commodity cost benchmarks and cost-per-beneficiary
        norms against state-stratified benchmarks in commodity_benchmarks.csv.
        - Checks itemized physical goods (Food, Medical, Relief Kits, Materials, Shelter) vs state rates.
        - Checks project cost-per-beneficiary vs state benchmark norm.
        - Fallback: 65/100 if no benchmark data or project state is available.
        """
        # Support legacy override if manual variance dictionary is provided
        if external_benchmarks is not None and "average_benchmark_variance_pct" in external_benchmarks:
            benchmark_variance = external_benchmarks["average_benchmark_variance_pct"]
            c_score = max(0.0, min(100.0, 100.0 - abs(benchmark_variance) * 2.0))
            return c_score, f"External cost context scored against manual benchmark index (variance: {benchmark_variance:+.1f}%)."

        if self.benchmarks_df is None:
            return 65.0, "No applicable external benchmark data was available."

        if project_data is None:
            project_data = {}

        state = str(project_data.get("location_state_primary", "")).strip().lower()
        if state in self.benchmarks_df.index:
            bench_row = self.benchmarks_df.loc[state].to_dict()
            state_display = self.benchmarks_df.loc[state]["state"]
        elif self.national_benchmarks is not None:
            bench_row = self.national_benchmarks
            state_display = "National Average"
        else:
            return 65.0, "State benchmark could not be determined."

        notes = []

        # 1. Physical Commodity Line Items Evaluation
        commodity_scores = []
        COMMODITY_MAP = {
            "food": "food_kit_cost_inr",
            "medical": "medical_kit_cost_inr",
            "relief kits": "relief_kit_cost_inr",
            "shelter": "shelter_kit_cost_inr",
            "materials": "education_materials_cost_inr"
        }

        if line_items is not None and len(line_items) > 0:
            items_df = pd.DataFrame(line_items) if not isinstance(line_items, pd.DataFrame) else line_items
            if "category" in items_df.columns and "unit_cost_inr" in items_df.columns:
                for _, item in items_df.iterrows():
                    cat = str(item.get("category", "")).strip().lower()
                    unit_cost = float(item.get("unit_cost_inr", 0))

                    if cat == "food":
                        # Food unit in projects is typically per-meal or per-ration unit (norm: INR 20-80)
                        if unit_cost <= 80.0:
                            commodity_scores.append(100.0)
                        elif unit_cost <= 150.0:
                            commodity_scores.append(85.0)
                        else:
                            commodity_scores.append(max(30.0, 85.0 - (unit_cost - 150.0) * 0.5))
                            notes.append(f"Food unit rate INR {unit_cost:,.1f} exceeds standard meal benchmark")
                    elif cat in COMMODITY_MAP:
                        bench_col = COMMODITY_MAP[cat]
                        bench_cost = float(bench_row.get(bench_col, 0))
                        if bench_cost > 0 and unit_cost > 0:
                            if unit_cost <= bench_cost * 1.20:
                                commodity_scores.append(100.0)
                            elif unit_cost <= bench_cost * 2.0:
                                commodity_scores.append(100.0 - (unit_cost / bench_cost - 1.20) * (30.0 / 0.80))
                            else:
                                commodity_scores.append(max(20.0, 70.0 - (unit_cost / bench_cost - 2.0) * 20.0))
                                notes.append(f"{cat.title()} rate INR {unit_cost:,.0f} vs {state_display} norm INR {bench_cost:,.0f}")

        # 2. Project Cost-per-Beneficiary vs State Benchmark Norm
        submitted_budget = float(project_data.get("submitted_budget") or project_data.get("expected_budget_inr") or 0)
        beneficiaries = float(project_data.get("beneficiaries_reported", 0))
        bench_cpb = float(bench_row.get("avg_cost_per_beneficiary_inr", 5500.0))

        if beneficiaries > 0 and submitted_budget > 0:
            actual_cpb = submitted_budget / beneficiaries
            cpb_ratio = actual_cpb / bench_cpb

            if 0.5 <= cpb_ratio <= 1.5:
                cpb_score = 100.0
            elif cpb_ratio < 0.5:
                cpb_score = max(50.0, 100.0 - (0.5 - cpb_ratio) * 100.0)
            elif cpb_ratio <= 2.2:
                cpb_score = max(40.0, 100.0 - (cpb_ratio - 1.5) * (60.0 / 0.7))
            else:
                cpb_score = max(10.0, 40.0 - (cpb_ratio - 2.2) * 15.0)
                notes.append(f"Cost per beneficiary (INR {actual_cpb:,.0f}) is {cpb_ratio:.1f}x state benchmark")
        else:
            cpb_score = 70.0
            actual_cpb = 0.0

        if len(commodity_scores) > 0:
            avg_comm = float(np.mean(commodity_scores))
            final_c = 0.50 * avg_comm + 0.50 * cpb_score
            explanation = f"Cost context ({final_c:.1f}/100) verified against {state_display} commodity benchmark (commodity score: {avg_comm:.1f}, cost/beneficiary: INR {actual_cpb:,.0f} vs norm INR {bench_cpb:,.0f})."
        else:
            final_c = cpb_score
            explanation = f"Cost context ({final_c:.1f}/100) verified against {state_display} benchmark norm (cost/beneficiary: INR {actual_cpb:,.0f} vs norm INR {bench_cpb:,.0f})."

        final_c = max(0.0, min(100.0, round(final_c, 2)))
        if notes:
            explanation += f" Notes: {'; '.join(notes[:2])}."
        return final_c, explanation

    def calculate_implementation_capacity(self, project_data):
        """
        Component I (15%): Evaluates NGO demonstrated organizational capacity.
        First-time NGOs receive a neutral/mid-range score (55-65), not 0.
        Uses: ngo_age_years_at_start, prior_projects_count, prior_max_beneficiaries,
              has_prior_projects, number_of_operational_states, number_of_operational_districts.
        """
        ngo_age = float(project_data.get("ngo_age_years_at_start", 0))
        prior_projects = int(project_data.get("prior_projects_count", 0))
        prior_max_ben = float(project_data.get("prior_max_beneficiaries", 0) or 0)
        has_prior = bool(prior_projects > 0)
        states = int(project_data.get("number_of_operational_states", 1))
        districts = int(project_data.get("number_of_operational_districts", 1))

        if not has_prior:
            # Neutral baseline for new NGOs
            base_score = 55.0
            age_bonus = min(10.0, ngo_age * 2.0)
            geo_bonus = 5.0 if districts > 1 else 0.0
            i_score = min(68.0, base_score + age_bonus + geo_bonus)
            explanation = f"New NGO with no prior project history evaluated with neutral baseline ({i_score:.1f}/100, {ngo_age:.0f} yrs registered)."
            return i_score, explanation

        # Established NGO Scoring
        base_score = 65.0

        # Project Volume Track Record
        if prior_projects >= 5:
            project_bonus = 18.0
        elif prior_projects >= 3:
            project_bonus = 12.0
        elif prior_projects >= 1:
            project_bonus = 6.0
        else:
            project_bonus = 0.0

        # Beneficiary Volume Demonstrated
        if prior_max_ben >= 4000:
            ben_bonus = 10.0
        elif prior_max_ben >= 2000:
            ben_bonus = 6.0
        elif prior_max_ben >= 500:
            ben_bonus = 3.0
        else:
            ben_bonus = 0.0

        # Organizational Age Maturity
        age_bonus = min(10.0, ngo_age * 1.5)

        # Geographic Reach
        geo_bonus = min(6.0, (states * 1.5) + (districts * 0.5))

        i_score = min(100.0, base_score + project_bonus + ben_bonus + age_bonus + geo_bonus)
        explanation = f"Demonstrated capacity ({i_score:.1f}/100) supported by {prior_projects} prior projects (max {prior_max_ben:,.0f} beneficiaries), {ngo_age:.0f} years operational age across {districts} districts."
        return i_score, explanation

    @staticmethod
    def get_feasibility_label(score):
        """
        Individual 5-tier standard scale (DB-compatible lowercase):
          90–100 = high (very high feasibility)
          75–89  = high
          60–74  = moderate
          40–59  = low
          0–39   = very_low
        """
        s = round(score, 2)
        if s >= 90.0:
            return "high"
        elif s >= 75.0:
            return "high"
        elif s >= 60.0:
            return "moderate"
        elif s >= 40.0:
            return "low"
        else:
            return "very_low"

    def score_project(self, project_data, submitted_budget=None, line_items=None, external_benchmarks=None):
        """
        Complete end-to-end evaluation pipeline for a new or historical project proposal:
        1. Infers predicted_expected_budget via existing XGBoost pipeline
        2. Calculates B (40%), S (25%), C (20%), I (15%)
        3. Computes FS = 0.40B + 0.25S + 0.20C + 0.15I
        4. Returns all components, label, and transparent explanations
        """
        # Stand-in budget handling for backtesting
        if submitted_budget is None:
            submitted_budget = float(project_data.get("expected_budget_inr", 0))

        # Format input for existing XGBoost pipeline
        if isinstance(project_data, dict):
            input_df = pd.DataFrame([project_data])
        else:
            input_df = project_data.copy()

        # Step 1: Predict expected budget using existing XGBoost model
        predicted_expected_budget = float(self.pipeline.predict(input_df)[0])

        # Prepare project dict with submitted_budget
        proj_dict = dict(project_data) if not isinstance(project_data, dict) else project_data.copy()
        proj_dict["submitted_budget"] = submitted_budget

        # Step 2: Component Scores
        b_score, b_expl = self.calculate_budget_realism(submitted_budget, predicted_expected_budget, line_items)
        s_score, s_expl = self.calculate_project_scale(project_data)
        c_score, c_expl = self.calculate_cost_context(project_data=proj_dict, line_items=line_items, external_benchmarks=external_benchmarks)
        i_score, i_expl = self.calculate_implementation_capacity(project_data)

        # Step 3: Final Feasibility Score Formula
        # FS = 0.40B + 0.25S + 0.20C + 0.15I
        feasibility_score = (0.40 * b_score) + (0.25 * s_score) + (0.20 * c_score) + (0.15 * i_score)
        feasibility_score = max(0.0, min(100.0, round(feasibility_score, 2)))

        feasibility_label = self.get_feasibility_label(feasibility_score)

        return {
            "submitted_budget": submitted_budget,
            "predicted_expected_budget": predicted_expected_budget,
            "deviation_pct": abs(submitted_budget - predicted_expected_budget) / max(predicted_expected_budget, 1.0) * 100.0,
            "B_score": round(b_score, 2),
            "S_score": round(s_score, 2),
            "C_score": round(c_score, 2),
            "I_score": round(i_score, 2),
            "feasibility_score": feasibility_score,
            "feasibility_label": feasibility_label,
            "explanations": {
                "B": b_expl,
                "S": s_expl,
                "C": c_expl,
                "I": i_expl
            }
        }


def run_batch_evaluation():
    """
    Backtests the feasibility scoring engine across the full 743 projects dataset
    using expected_budget_inr as the stand-in for submitted_budget.
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(curr_dir)
    data_dir = os.path.join(base_dir, "feasibility_data")
    feat_path = os.path.join(data_dir, "feasibility_features.csv") if os.path.exists(os.path.join(data_dir, "feasibility_features.csv")) else os.path.join(data_dir, "feasibility_features (1).csv")
    targ_path = os.path.join(data_dir, "feasibility_targets.csv") if os.path.exists(os.path.join(data_dir, "feasibility_targets.csv")) else os.path.join(data_dir, "feasibility_targets (1).csv")
    budget_items_path = os.path.join(data_dir, "project_budget_items.csv") if os.path.exists(os.path.join(data_dir, "project_budget_items.csv")) else os.path.join(data_dir, "project_budget_items (1).csv")

    feat_df = pd.read_csv(feat_path)
    targ_df = pd.read_csv(targ_path)
    df = pd.merge(feat_df, targ_df, on="project_id", how="inner")

    # Load budget items if available
    budget_items_df = None
    if os.path.exists(budget_items_path):
        budget_items_df = pd.read_csv(budget_items_path)

    scorer = FeasibilityScorer()
    print("Evaluating Feasibility Scores across all 743 projects...")

    results = []
    for idx, row in df.iterrows():
        p_id = row["project_id"]
        sub_budget = float(row["expected_budget_inr"])
        p_items = None
        if budget_items_df is not None:
            p_items = budget_items_df[budget_items_df["project_id"] == p_id]

        res = scorer.score_project(row.to_dict(), submitted_budget=sub_budget, line_items=p_items)
        results.append({
            "project_id": p_id,
            "submitted_budget": sub_budget,
            "predicted_expected_budget": res["predicted_expected_budget"],
            "deviation_pct": res["deviation_pct"],
            "B_score": res["B_score"],
            "S_score": res["S_score"],
            "C_score": res["C_score"],
            "I_score": res["I_score"],
            "feasibility_score": res["feasibility_score"],
            "feasibility_label": res["feasibility_label"]
        })

    res_df = pd.DataFrame(results)
    out_csv = os.path.join(outputs_dir, "feasibility_scores.csv")
    try:
        res_df.to_csv(out_csv, index=False, float_format="%.2f")
        print(f"Saved full feasibility scores to: {out_csv}")
    except PermissionError:
        alt_csv = os.path.join(outputs_dir, "feasibility_scores_updated.csv")
        res_df.to_csv(alt_csv, index=False, float_format="%.2f")
        print(f"Note: '{out_csv}' is currently open in Excel or another app.")
        print(f"Saved to '{alt_csv}' instead. Close the file in Excel to allow overwriting.")

    print("\nFeasibility Score Distribution:")
    print(res_df["feasibility_label"].value_counts())
    print("\nSummary Statistics:")
    print(res_df[["B_score", "S_score", "C_score", "I_score", "feasibility_score"]].describe())


if __name__ == "__main__":
    run_batch_evaluation()
