"""
Eleos Feasibility System - Interactive Demo / Verification Script
Demonstrates end-to-end feasibility scoring for brand-new project proposals:
Project Details + submitted_budget
  -> Feature Engineering
  -> Existing XGBoost
  -> Predicted Expected Budget
  -> B / S / C / I Scores
  -> Final Feasibility Score & Label
"""

import json
from feasibility_scoring import FeasibilityScorer


def run_demo():
    print("=" * 80)
    print("ELEOS FEASIBILITY SYSTEM: NEW PROJECT PROPOSAL EVALUATION DEMO")
    print("Formula: FS = 0.40*B + 0.25*S + 0.20*C + 0.15*I")
    print("=" * 80)

    scorer = FeasibilityScorer()

    # Case 1: Realistic, well-aligned proposal from an established NGO
    case_1_project = {
        "primary_sector": "Healthcare & Nutrition",
        "secondary_sectors": '["Social Welfare & Community Development"]',
        "location_state_primary": "Maharashtra",
        "location_district_primary": "Pune",
        "is_remote_area": False,
        "is_disaster_relief": False,
        "duration_months": 18,
        "beneficiaries_reported": 3200,
        "villages_covered": 12,
        "milestones_reported": 5,
        "ngo_age_years_at_start": 5,
        "number_of_operational_states": 2,
        "number_of_operational_districts": 4,
        "number_of_sectors": 2,
        "prior_projects_count": 4,
        "prior_max_beneficiaries": 3500.0
    }
    case_1_submitted_budget = 7_500_000.0  # ₹75 Lakhs (realistic)

    # Case 2: Overpriced proposal (submitted budget is ~2.5x the realistic cost)
    case_2_project = case_1_project.copy()
    case_2_submitted_budget = 19_000_000.0  # ₹1.9 Crore (heavily inflated)

    # Case 3: First-time NGO (zero prior projects, no prior history, neutral I)
    case_3_project = {
        "primary_sector": "Education & Skill Development",
        "secondary_sectors": '["Social Welfare & Community Development"]',
        "location_state_primary": "Karnataka",
        "location_district_primary": "Bengaluru Urban",
        "is_remote_area": False,
        "is_disaster_relief": False,
        "duration_months": 12,
        "beneficiaries_reported": 1200,
        "villages_covered": 6,
        "milestones_reported": 4,
        "ngo_age_years_at_start": 1,
        "number_of_operational_states": 1,
        "number_of_operational_districts": 1,
        "number_of_sectors": 2,
        "prior_projects_count": 0,
        "prior_max_beneficiaries": None  # Missing history
    }
    case_3_submitted_budget = 1_800_000.0  # ₹18 Lakhs (aligned with starter project)

    # Case 4: Scale-stressed first-time NGO (aiming for 10,000 beneficiaries in 4 months)
    case_4_project = {
        "primary_sector": "Water, Sanitation & Environment",
        "secondary_sectors": '["Emergency Relief & Rehabilitation"]',
        "location_state_primary": "West Bengal",
        "location_district_primary": "Kolkata",
        "is_remote_area": True,
        "is_disaster_relief": True,
        "duration_months": 3,
        "beneficiaries_reported": 9500,
        "villages_covered": 3,  # >3,000 per village in 3 months
        "milestones_reported": 2,
        "ngo_age_years_at_start": 0,
        "number_of_operational_states": 1,
        "number_of_operational_districts": 1,
        "number_of_sectors": 2,
        "prior_projects_count": 0,
        "prior_max_beneficiaries": 0.0
    }
    case_4_submitted_budget = 12_000_000.0

    proposals = [
        ("Proposal 1: Established NGO with Realistic Budget", case_1_project, case_1_submitted_budget),
        ("Proposal 2: Overpriced Proposal (Same Project as #1, but 2.5x Budget)", case_2_project, case_2_submitted_budget),
        ("Proposal 3: First-Time NGO (Zero Prior History, Neutral Capacity)", case_3_project, case_3_submitted_budget),
        ("Proposal 4: Overcompressed & Scale-Stressed First-Time Project", case_4_project, case_4_submitted_budget)
    ]

    for title, proj, sub_budget in proposals:
        print("\n" + "-" * 80)
        print(f"EVALUATING: {title}")
        print(f"  Submitted Budget: INR {sub_budget:,.2f}")
        print(f"  Scope: {proj['beneficiaries_reported']:,} beneficiaries, {proj['villages_covered']} villages, {proj['duration_months']} months")
        print(f"  NGO Track Record: {proj.get('prior_projects_count', 0)} prior projects, {proj.get('ngo_age_years_at_start', 0)} yrs age")

        res = scorer.score_project(proj, submitted_budget=sub_budget)

        print("\n  [XGBoost Prediction]")
        print(f"    Predicted Expected Budget: INR {res['predicted_expected_budget']:,.2f}")
        print(f"    Budget Deviation         : {res['deviation_pct']:.1f}%")

        print("\n  [Pillar Component Breakdown (0-100)]")
        print(f"    B - Budget Realism       (40%): {res['B_score']:>6.2f} / 100 | {res['explanations']['B']}")
        print(f"    S - Project Scale        (25%): {res['S_score']:>6.2f} / 100 | {res['explanations']['S']}")
        print(f"    C - Cost Context         (20%): {res['C_score']:>6.2f} / 100 | {res['explanations']['C']}")
        print(f"    I - Implementation Cap.  (15%): {res['I_score']:>6.2f} / 100 | {res['explanations']['I']}")

        print("\n  ==================================================================")
        print(f"  >>> FINAL FEASIBILITY SCORE : {res['feasibility_score']:.2f} / 100")
        print(f"  >>> FEASIBILITY LABEL       : {res['feasibility_label']}")
        print("  ==================================================================")


if __name__ == "__main__":
    run_demo()
