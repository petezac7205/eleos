"""
Eleos Feasibility System - Inference Verification Script
Demonstrates passing brand-new project proposals to the trained XGBoost pipeline
to receive realistic expected budget predictions (expected_budget_inr).
"""

import os
import pickle
import pandas as pd

# Import transformer class definitions so pickle can unpickle cleanly
from train_xgb_budget import EleosFeatureEngineer, EleosBudgetPredictor, ALL_SECTORS


def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(curr_dir)
    model_path = os.path.join(base_dir, "models", "xgb_budget_pipeline.pkl")
    if not os.path.exists(model_path):
        model_path = os.path.join(curr_dir, "xgb_budget_pipeline.pkl")

    print("=" * 70)
    print("ELEOS FEASIBILITY SYSTEM: NEW PROJECT BUDGET INFERENCE TEST")
    print("=" * 70)
    print(f"Loading trained pipeline from: {model_path}")
    with open(model_path, "rb") as f:
        pipeline = pickle.load(f)
    print("Pipeline loaded successfully!\n")

    # Scenario 1: Established NGO with prior project track record and disaster relief
    established_ngo_project = {
        "primary_sector": "Disaster Relief & Rehabilitation",
        "secondary_sectors": '["Healthcare & Medical", "Rural Development"]',
        "location_state_primary": "West Bengal",
        "location_district_primary": "Kolkata",
        "is_remote_area": True,
        "is_disaster_relief": True,
        "duration_months": 18,
        "beneficiaries_reported": 4500,
        "villages_covered": 15,
        "milestones_reported": 5,
        "ngo_age_years_at_start": 4,
        "number_of_operational_states": 2,
        "number_of_operational_districts": 3,
        "number_of_sectors": 3,
        "prior_projects_count": 5,
        "prior_max_beneficiaries": 4737.0
    }

    # Scenario 2: Brand-New NGO (0 prior projects, no prior beneficiaries history)
    new_ngo_project = {
        "primary_sector": "Education",
        "secondary_sectors": '["Child Welfare"]',
        "location_state_primary": "Maharashtra",
        "location_district_primary": "Pune",
        "is_remote_area": False,
        "is_disaster_relief": False,
        "duration_months": 12,
        "beneficiaries_reported": 1200,
        "villages_covered": 5,
        "milestones_reported": 3,
        "ngo_age_years_at_start": 0,
        "number_of_operational_states": 1,
        "number_of_operational_districts": 1,
        "number_of_sectors": 1,
        "prior_projects_count": 0,
        "prior_max_beneficiaries": None  # Missing history explicitly tested
    }

    # Scenario 3: Large-scale Environment & Water project
    environment_project = {
        "primary_sector": "Environment & Forests",
        "secondary_sectors": '["Water & Sanitation", "Rural Development"]',
        "location_state_primary": "Tamil Nadu",
        "location_district_primary": "Coimbatore",
        "is_remote_area": True,
        "is_disaster_relief": False,
        "duration_months": 24,
        "beneficiaries_reported": 3500,
        "villages_covered": 18,
        "milestones_reported": 4,
        "ngo_age_years_at_start": 5,
        "number_of_operational_states": 2,
        "number_of_operational_districts": 4,
        "number_of_sectors": 3,
        "prior_projects_count": 3,
        "prior_max_beneficiaries": 3000.0
    }

    test_cases = [
        ("Established NGO (Disaster Relief in Remote Area)", established_ngo_project),
        ("First-Time NGO (Zero Prior History, Missing Prior Max)", new_ngo_project),
        ("Large-Scale Environmental Initiative", environment_project)
    ]

    for title, test_input in test_cases:
        print("-" * 70)
        print(f"Proposal: {title}")
        print(f"  Primary Sector       : {test_input['primary_sector']}")
        print(f"  Secondary Sectors   : {test_input['secondary_sectors']}")
        print(f"  Location            : {test_input['location_district_primary']}, {test_input['location_state_primary']}")
        print(f"  Duration            : {test_input['duration_months']} months")
        print(f"  Beneficiaries       : {test_input['beneficiaries_reported']}")
        print(f"  Prior Projects Count: {test_input['prior_projects_count']}")
        print(f"  Prior Max Benefic.  : {test_input['prior_max_beneficiaries']}")

        # Inference call via unified pipeline
        predicted_budget = pipeline.predict(test_input)[0]

        print(f"\n  >>> PREDICTED EXPECTED BUDGET: INR {predicted_budget:,.2f}")
        assert predicted_budget > 0, "Budget prediction must be strictly positive!"
        print("  >>> Plausibility Check: PASSED (Budget > 0, safely handled)\n")

    # Batch test via DataFrame
    batch_df = pd.DataFrame([tc[1] for tc in test_cases])
    batch_predictions = pipeline.predict(batch_df)
    print("=" * 70)
    print("Batch DataFrame Prediction Test:")
    for idx, (title, _) in enumerate(test_cases):
        print(f"  [{idx+1}] {title:<45} -> INR {batch_predictions[idx]:,.2f}")
    print("=" * 70)
    print("All inference tests completed successfully!")


if __name__ == "__main__":
    main()
