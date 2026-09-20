"""
Eleos Feasibility & Expected Budget Calculation Service
-------------------------------------------------------
Ingests campaign proposal and NGO compliance data from the frontend form,
defensively sanitizes inputs with safe fallbacks for missing fields,
computes the realistic expected budget via XGBoost, and calculates
the multi-pillar Feasibility Score (0-100) with detailed pillar breakdowns.

Outputs a clean JSON payload ready for direct frontend consumption.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

# Ensure scripts directory is on sys.path for internal imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from feasibility_scoring import FeasibilityScorer, ALL_SECTORS


# Canonical Sector Mapping (normalizes legacy, full, or partial sector names)
SECTOR_MAP = {
    "healthcare & medical": "Healthcare & Nutrition",
    "healthcare": "Healthcare & Nutrition",
    "medical": "Healthcare & Nutrition",
    "nutrition & food security": "Healthcare & Nutrition",
    "nutrition": "Healthcare & Nutrition",
    "food security": "Healthcare & Nutrition",
    "healthcare & nutrition": "Healthcare & Nutrition",

    "education": "Education & Skill Development",
    "skill development & livelihood": "Education & Skill Development",
    "skill development": "Education & Skill Development",
    "livelihood": "Education & Skill Development",
    "education & skill development": "Education & Skill Development",

    "child welfare": "Social Welfare & Community Development",
    "women empowerment": "Social Welfare & Community Development",
    "rural development": "Social Welfare & Community Development",
    "community development": "Social Welfare & Community Development",
    "social welfare": "Social Welfare & Community Development",
    "social welfare & community development": "Social Welfare & Community Development",

    "water & sanitation": "Water, Sanitation & Environment",
    "water": "Water, Sanitation & Environment",
    "sanitation": "Water, Sanitation & Environment",
    "environment & forests": "Water, Sanitation & Environment",
    "environment": "Water, Sanitation & Environment",
    "water, sanitation & environment": "Water, Sanitation & Environment",

    "disaster relief & rehabilitation": "Emergency Relief & Rehabilitation",
    "disaster relief": "Emergency Relief & Rehabilitation",
    "emergency relief": "Emergency Relief & Rehabilitation",
    "rehabilitation": "Emergency Relief & Rehabilitation",
    "emergency relief & rehabilitation": "Emergency Relief & Rehabilitation",

    # Catch-all for legacy/unknown
    "other": "Social Welfare & Community Development"
}


def normalize_sector(sector_name: Optional[str]) -> str:
    """Safely normalizes any sector input into one of the 5 canonical macro-categories."""
    if not sector_name:
        return "Social Welfare & Community Development"
    cleaned = str(sector_name).strip().lower()
    return SECTOR_MAP.get(cleaned, "Social Welfare & Community Development")


def format_inr(amount: float) -> str:
    """Formats an amount into Indian Rupees representation (Lakhs / Crores)."""
    val = float(amount)
    if val >= 10000000:
        return f"INR {val / 10000000:.2f} Cr"
    elif val >= 100000:
        return f"INR {val / 100000:.2f} Lakhs"
    else:
        return f"INR {val:,.2f}"


class CampaignFeasibilityEvaluator:
    """
    Evaluator that sanitizes raw frontend form payloads and produces
    expected budget predictions and feasibility scores.
    """

    def __init__(self, model_path: Optional[str] = None, benchmarks_path: Optional[str] = None):
        self.scorer = FeasibilityScorer(model_path=model_path, benchmarks_path=benchmarks_path)
        self._load_ngo_history_cache()

    def _load_ngo_history_cache(self):
        """Loads historical NGO track record cache if available for auto-filling existing NGOs."""
        self.ngo_history = {}
        base_dir = os.path.dirname(CURRENT_DIR)
        feat_path = os.path.join(base_dir, "feasibility_data", "feasibility_features.csv")
        if not os.path.exists(feat_path):
            feat_path = os.path.join(base_dir, "feasibility_data", "feasibility_features (1).csv")
        if os.path.exists(feat_path):
            try:
                df = pd.read_csv(feat_path)
                grouped = df.groupby("ngo_id")
                for ngo_id, group in grouped:
                    self.ngo_history[str(ngo_id).strip()] = {
                        "prior_projects_count": int(group["prior_projects_count"].max() + 1),
                        "prior_max_beneficiaries": float(group["beneficiaries_reported"].max()),
                        "number_of_operational_states": int(group["number_of_operational_states"].max()),
                        "number_of_operational_districts": int(group["number_of_operational_districts"].max()),
                        "ngo_age_years_at_start": float(group["ngo_age_years_at_start"].max() + 1)
                    }
            except Exception:
                pass

    def sanitize_payload(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts, converts, and sanitizes input data from the frontend form.
        Any missing or omitted fields receive safe, defensible defaults.
        """
        # 1. Campaign Identity
        project_name = str(raw_data.get("title") or raw_data.get("project_name") or raw_data.get("campaign_title") or "Community Campaign").strip()
        ngo_id = str(raw_data.get("ngo_id") or "NGO_FIRST_TIME").strip()

        # 2. Sector Normalization
        primary_sector = normalize_sector(raw_data.get("primary_sector") or raw_data.get("category") or raw_data.get("cause"))
        raw_sec = raw_data.get("secondary_sectors") or []
        if isinstance(raw_sec, str):
            try:
                raw_sec = json.loads(raw_sec)
            except Exception:
                raw_sec = [s.strip() for s in raw_sec.replace("[", "").replace("]", "").replace("'", "").replace('"', "").split(",") if s.strip()]

        normalized_secondary = []
        for sec in raw_sec:
            norm_sec = normalize_sector(sec)
            if norm_sec != primary_sector and norm_sec not in normalized_secondary:
                normalized_secondary.append(norm_sec)

        # 3. Location
        state = str(raw_data.get("location_state") or raw_data.get("location_state_primary") or raw_data.get("state") or "Maharashtra").strip()
        district = str(raw_data.get("location_district") or raw_data.get("location_district_primary") or raw_data.get("district") or "Default District").strip()

        # 4. Dates & Duration
        start_date = raw_data.get("start_date")
        end_date = raw_data.get("end_date")
        duration_months = 6.0
        duration_days = 180

        if start_date and end_date:
            try:
                s_dt = datetime.strptime(str(start_date)[:10], "%Y-%m-%d")
                e_dt = datetime.strptime(str(end_date)[:10], "%Y-%m-%d")
                duration_days = max(1, (e_dt - s_dt).days)
                duration_months = max(1.0, round(duration_days / 30.0))
            except Exception:
                duration_months = float(raw_data.get("duration_months") or 6.0)
        elif raw_data.get("duration_months"):
            duration_months = max(1.0, float(raw_data.get("duration_months")))
            duration_days = int(duration_months * 30)

        # 5. Flags
        urgency = str(raw_data.get("urgency_level") or raw_data.get("urgency") or "").strip().lower()
        is_disaster = bool(
            raw_data.get("is_disaster_relief") or
            urgency in ["emergency", "emergency/disaster", "disaster"] or
            primary_sector == "Emergency Relief & Rehabilitation"
        )
        is_remote = bool(raw_data.get("is_remote_area") or False)

        # 6. Scope
        beneficiaries = max(1.0, float(raw_data.get("beneficiaries_count") or raw_data.get("beneficiaries_reported") or raw_data.get("beneficiaries") or raw_data.get("target_beneficiaries") or 500))
        villages = max(1.0, float(raw_data.get("communities_count") or raw_data.get("villages_covered") or raw_data.get("communities") or raw_data.get("communities_covered") or 1))
        
        milestones_val = raw_data.get("milestones_reported") or raw_data.get("planned_milestones")
        if not milestones_val and isinstance(raw_data.get("milestones"), list):
            milestones_val = len(raw_data.get("milestones"))
        milestones = max(1.0, float(milestones_val or 3))

        # 7. Financial Target
        submitted_budget = float(
            raw_data.get("target_amount") or
            raw_data.get("submitted_budget") or
            raw_data.get("requested_budget") or
            raw_data.get("fundraising_target") or
            0.0
        )

        # 8. NGO History (Lookup cache or fallback to starter/first-time defaults)
        history = self.ngo_history.get(ngo_id, {})
        prior_projects = int(raw_data.get("prior_projects_count", history.get("prior_projects_count", 0)))
        prior_max_ben = float(raw_data.get("prior_max_beneficiaries", history.get("prior_max_beneficiaries", 0.0)) or 0.0)
        ngo_age = float(raw_data.get("ngo_age_years_at_start", history.get("ngo_age_years_at_start", 1.0)))
        states_count = int(raw_data.get("number_of_operational_states", history.get("number_of_operational_states", 1)))
        districts_count = int(raw_data.get("number_of_operational_districts", history.get("number_of_operational_districts", 1)))

        # 9. Line Items / Commodities (if provided)
        line_items = raw_data.get("line_items") or raw_data.get("commodities") or None

        sanitized = {
            "project_name": project_name,
            "ngo_id": ngo_id,
            "primary_sector": primary_sector,
            "secondary_sectors": json.dumps(normalized_secondary),
            "location_state_primary": state,
            "location_district_primary": district,
            "start_date": str(start_date) if start_date else "2025-01-01",
            "end_date": str(end_date) if end_date else "2025-07-01",
            "duration_months": duration_months,
            "duration_days": duration_days,
            "is_remote_area": is_remote,
            "is_disaster_relief": is_disaster,
            "beneficiaries_reported": beneficiaries,
            "villages_covered": villages,
            "milestones_reported": milestones,
            "submitted_budget": submitted_budget,
            "prior_projects_count": prior_projects,
            "prior_max_beneficiaries": prior_max_ben,
            "ngo_age_years_at_start": ngo_age,
            "number_of_operational_states": states_count,
            "number_of_operational_districts": districts_count,
            "number_of_sectors": 1 + len(normalized_secondary),
            "line_items": line_items
        }
        return sanitized

    def evaluate(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        End-to-end evaluation:
        1. Sanitizes inputs with safe defaults
        2. Calculates expected budget via XGBoost
        3. Computes 4-pillar feasibility score and explanations
        4. Packages clean response formatted for frontend UI
        """
        clean_data = self.sanitize_payload(raw_payload)
        submitted_budget = clean_data["submitted_budget"]
        line_items = clean_data.get("line_items")

        # Score project
        score_res = self.scorer.score_project(
            project_data=clean_data,
            submitted_budget=submitted_budget if submitted_budget > 0 else None,
            line_items=line_items
        )

        predicted_budget = score_res["predicted_expected_budget"]
        final_score = score_res["feasibility_score"]
        label = score_res["feasibility_label"]
        explanations = score_res["explanations"]

        # If submitted budget wasn't provided, use predicted budget
        if submitted_budget <= 0:
            submitted_budget = predicted_budget
            deviation_pct = 0.0
        else:
            deviation_pct = score_res["deviation_pct"]

        # Construct Actionable Recommendations for NGO
        recommendations = []
        if deviation_pct > 25.0 and submitted_budget > predicted_budget:
            recommendations.append(
                f"Requested budget is {deviation_pct:.1f}% above model estimate ({format_inr(predicted_budget)}). Consider calibrating line-item costs to improve feasibility."
            )
        if score_res["S_score"] < 75.0:
            recommendations.append("Project scope shows high beneficiary density or aggressive delivery timeline. Expanding duration or village footprint will enhance credibility.")
        if score_res["C_score"] < 75.0:
            recommendations.append("Unit costs exceed state procurement benchmarks. Review physical commodity line items against local wholesale norms.")

        if not recommendations:
            recommendations.append("Proposal is well-aligned with regional benchmarks and realistic operational capacity.")

        response = {
            "status": "success",
            "campaign_title": clean_data["project_name"],
            "primary_sector": clean_data["primary_sector"],
            "location_state": clean_data["location_state_primary"],
            "expected_budget_inr": round(predicted_budget, 2),
            "expected_budget_formatted": format_inr(predicted_budget),
            "submitted_budget_inr": round(submitted_budget, 2),
            "submitted_budget_formatted": format_inr(submitted_budget),
            "budget_deviation_pct": round(deviation_pct, 1),
            "feasibility_score": final_score,
            "feasibility_label": label,
            "is_feasible": bool(final_score >= 60.0),
            "pillars": {
                "budget_realism": {
                    "score": score_res["B_score"],
                    "weight": "40%",
                    "explanation": explanations.get("B", "")
                },
                "project_scale": {
                    "score": score_res["S_score"],
                    "weight": "25%",
                    "explanation": explanations.get("S", "")
                },
                "cost_context": {
                    "score": score_res["C_score"],
                    "weight": "20%",
                    "explanation": explanations.get("C", "")
                },
                "implementation_capacity": {
                    "score": score_res["I_score"],
                    "weight": "15%",
                    "explanation": explanations.get("I", "")
                }
            },
            "recommendations": recommendations
        }
        return response


# Global instance for direct module imports
evaluator = CampaignFeasibilityEvaluator()


def evaluate_campaign(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for external imports."""
    return evaluator.evaluate(payload)


def run_cli():
    parser = argparse.ArgumentParser(description="Eleos Campaign Feasibility & Budget Calculator")
    parser.add_argument("--json", type=str, help="Raw JSON payload string")
    parser.add_argument("--file", type=str, help="Path to input JSON file")
    parser.add_argument("--demo", action="store_true", help="Run with a sample frontend proposal")
    args = parser.parse_args()

    if args.demo:
        sample = {
            "campaign_title": "Primary Healthcare & Nutrition Support for Rural Children",
            "primary_sector": "Healthcare & Nutrition",
            "secondary_sectors": ["Social Welfare & Community Development"],
            "location_state_primary": "Maharashtra",
            "location_district_primary": "Pune",
            "is_remote_area": False,
            "is_disaster_relief": False,
            "start_date": "2025-06-01",
            "end_date": "2026-06-01",
            "beneficiaries_reported": 3500,
            "villages_covered": 14,
            "milestones_reported": 4,
            "submitted_budget": 8500000.0,
            "commodities": [
                {"category": "Food", "unit_cost_inr": 2200, "quantity": 1000},
                {"category": "Medical", "unit_cost_inr": 950, "quantity": 1500}
            ]
        }
        output = evaluate_campaign(sample)
        print(json.dumps(output, indent=2))
        return

    payload = {}
    if args.file:
        with open(args.file, "r") as f:
            payload = json.load(f)
    elif args.json:
        payload = json.loads(args.json)
    elif not sys.stdin.isatty():
        payload = json.load(sys.stdin)
    else:
        print("Error: Provide input via --json, --file, stdin, or use --demo.")
        sys.exit(1)

    output = evaluate_campaign(payload)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    run_cli()
