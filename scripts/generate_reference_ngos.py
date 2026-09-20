"""
ELEOS — Member 1: Synthetic Data Generator
Generates realistic, accounting-consistent synthetic datasets for 200 Indian NGOs across:
1. ngo_registry_raw (Dataset A)
2. ngo_master (Dataset B)
3. ngo_public_profile (Dataset C)
4. financial_reports (Dataset D)
5. ngo_projects (Dataset E)
6. evidence_documents (Dataset G)

IMPORTANT METHODOLOGICAL NOTE:
Synthetic data is a validation, pipeline-testing, and demonstration tool only.
It does NOT constitute evidence of real-world validity or non-profit integrity.
Real-world deployment strictly requires verified statutory and regulatory filing data.
"""

import os
import json
import random
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

# Fixed random seed for complete reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "synthetic"
DATA_DIR = ROOT_DIR / "data" / "reference"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Indian States & District samples
STATES_AND_DISTRICTS = {
    "Tamil Nadu": ["Chennai", "Vellore", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Raigad", "Thane"],
    "Karnataka": ["Bengaluru Urban", "Mysuru", "Dharwad", "Belagavi", "Mangaluru"],
    "Delhi": ["New Delhi", "Central Delhi", "South Delhi", "North Delhi"],
    "West Bengal": ["Kolkata", "Howrah", "North 24 Parganas", "Darjeeling"],
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Kanpur Nagar", "Noida", "Prayagraj"],
    "Kerala": ["Thiruvananthapuram", "Ernakulam", "Kozhikode", "Thrissur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Odisha": ["Khordha", "Cuttack", "Sundargarh", "Puri"]
}

SECTORS = [
    "Education",
    "Healthcare & Medical",
    "Nutrition & Food Security",
    "Disaster Relief & Rehabilitation",
    "Environment & Forests",
    "Rural Development",
    "Women Empowerment",
    "Child Welfare",
    "Skill Development & Livelihood",
    "Water & Sanitation"
]

REGISTRATION_TYPES = ["Trust", "Society", "Section 8"]
REGISTRATION_AUTHORITIES = {
    "Trust": "Sub-Registrar / Charity Commissioner",
    "Society": "Registrar of Societies",
    "Section 8": "Ministry of Corporate Affairs (MCA)"
}

ACT_NAMES = {
    "Trust": "Indian Trusts Act, 1882",
    "Society": "Societies Registration Act, 1860",
    "Section 8": "Companies Act, 2013"
}

NGO_PREFIXES = [
    "Asha", "Navjeevan", "Seva", "Samarpan", "Vikas", "Umeed", "Prerna",
    "Jan Kalyan", "Gramin", "Punarutthan", "Sankalp", "Uday", "Sahyog",
    "Deepam", "Kavach", "Goonj", "Sneha", "Kalyan", "Shakti", "Manav"
]

NGO_SUFFIXES = [
    "Foundation", "Trust", "Society", "Samiti", "Association",
    "Network", "Sansthan", "Mission", "Initiative", "Seva Sanstha"
]

AUDITORS = [
    "M/s R. K. Sharma & Associates, Chartered Accountants",
    "M/s V. Raman & Co., Chartered Accountants",
    "M/s Deshmukh & Associates, Chartered Accountants",
    "M/s Iyer, Natarajan & Co., Chartered Accountants",
    "M/s Gupta & Aggarwal, Chartered Accountants",
    "M/s Sen & Dasgupta, Chartered Accountants",
    "M/s K. Mehta & Co., Chartered Accountants"
]


def generate_pan(entity_type: str) -> str:
    """Generates realistic Indian PAN (Permanent Account Number)."""
    # 4th letter: 'T' for Trust, 'A' for Society/AOP, 'C' for Section 8 Company
    char4 = "T" if entity_type == "Trust" else ("C" if entity_type == "Section 8" else "A")
    chars = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    digits = f"{random.randint(1000, 9999)}"
    last_char = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return f"{chars}{char4}{digits}{last_char}"


def generate_darpan_id(state: str, year: int) -> str:
    state_code = "".join([w[0].upper() for w in state.split()[:2]])
    if len(state_code) == 1:
        state_code = state[:2].upper()
    return f"{state_code}/{year}/{random.randint(1000000, 9999999)}"


def generate_reference_data(num_ngos: int = 200) -> Dict[str, pd.DataFrame]:
    """
    Generates realistic, balanced, and accounting-consistent non-profit records.
    Avoids artificial clustering, excessive class imbalance, and unrealistic feature skew.
    """
    print(f"[1/7] Generating core NGO population (N={num_ngos})...")

    registry_raw_rows = []
    ngo_master_rows = []
    ngo_public_profile_rows = []
    financial_report_rows = []
    ngo_project_rows = []
    evidence_document_rows = []

    current_date = date(2026, 9, 16)

    for i in range(1, num_ngos + 1):
        ngo_id = f"NGO_{i:05d}"
        source_uid = f"DARPAN_{random.randint(100000, 999999)}"

        # Generate Name
        base_name = f"{random.choice(NGO_PREFIXES)} {random.choice(NGO_SUFFIXES)}"
        if i <= 50:
            # Ensure diversity
            name = f"{base_name} {random.choice(['India', 'National', 'Gramin', 'Seva'])}"
        else:
            name = f"{base_name} {i}"
        
        normalized_name = " ".join(name.strip().upper().split())

        # Registration Geography
        reg_state = random.choice(list(STATES_AND_DISTRICTS.keys()))
        reg_district = random.choice(STATES_AND_DISTRICTS[reg_state])
        reg_subdistrict = f"{reg_district} Taluk"

        # Registration Type
        reg_type = random.choice(REGISTRATION_TYPES)
        reg_auth = REGISTRATION_AUTHORITIES[reg_type]
        act_name = ACT_NAMES[reg_type]
        reg_num = f"{reg_type[:3].upper()}/{random.randint(100, 999)}/{random.randint(1995, 2026)}/{random.randint(1000, 9999)}"

        # Age & Year of Registration (Continuous distribution)
        # 15% new (< 2 years), 25% young (2-5 years), 40% mid (5-15 years), 20% mature (> 15 years)
        age_cohort = random.random()
        if age_cohort < 0.15:
            age_years = round(random.uniform(0.1, 1.9), 1)
        elif age_cohort < 0.40:
            age_years = round(random.uniform(2.0, 4.9), 1)
        elif age_cohort < 0.80:
            age_years = round(random.uniform(5.0, 14.9), 1)
        else:
            age_years = round(random.uniform(15.0, 30.0), 1)

        year_established = int(current_date.year - age_years)
        reg_date = date(year_established, random.randint(1, 12), random.randint(1, 28))

        # Sectors (1 to 3 sectors per NGO)
        num_sectors = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
        ngo_sectors = random.sample(SECTORS, k=num_sectors)
        primary_sector = ngo_sectors[0]

        # Operational Reach (1 to 4 states)
        num_op_states = random.choices([1, 2, 3, 4], weights=[0.60, 0.25, 0.10, 0.05])[0]
        op_states = [reg_state]
        for _ in range(num_op_states - 1):
            s = random.choice(list(STATES_AND_DISTRICTS.keys()))
            if s not in op_states:
                op_states.append(s)

        op_districts = [reg_district]
        for s in op_states:
            num_d = random.randint(1, 3)
            sampled_d = random.sample(STATES_AND_DISTRICTS[s], k=min(num_d, len(STATES_AND_DISTRICTS[s])))
            for d in sampled_d:
                if d not in op_districts:
                    op_districts.append(d)

        # ---------------------------------------------------------------------
        # 1. Dataset A: ngo_registry_raw (Can contain multiple rows per NGO)
        # ---------------------------------------------------------------------
        # Create at least 1 raw record, sometimes 2 or 3 representing district filings
        num_raw_records = len(op_districts) if len(op_districts) <= 3 else 3
        for r_idx in range(num_raw_records):
            registry_raw_rows.append({
                "as_on_date": current_date.isoformat(),
                "unique_id": source_uid,
                "ngo_name": name if r_idx == 0 else f"{name} ({op_districts[r_idx]})",
                "ngo_email": f"contact@{name.lower().replace(' ', '')[:12]}.org" if random.random() > 0.1 else None,
                "state_of_registration": reg_state,
                "registered_district": reg_district,
                "registered_subdistrict": reg_subdistrict,
                "type_of_ngo": reg_type,
                "registration_authority": reg_auth,
                "registration_number": reg_num,
                "act_name": act_name,
                "date_of_registration": reg_date.isoformat(),
                "sectors": ", ".join(ngo_sectors),
                "operational_district": op_districts[r_idx],
                "operational_state": op_states[min(r_idx, len(op_states) - 1)],
                "source_url": f"https://ngodarpan.gov.in/index.php/home/statewise_ngo/{source_uid}"
            })

        # ---------------------------------------------------------------------
        # 2. Dataset B: ngo_master (1 row per NGO)
        # ---------------------------------------------------------------------
        ngo_master_rows.append({
            "ngo_id": ngo_id,
            "source_unique_id": source_uid,
            "ngo_name": name,
            "normalized_ngo_name": normalized_name,
            "registration_state": reg_state,
            "registered_district": reg_district,
            "registration_type": reg_type,
            "registration_authority": reg_auth,
            "registration_number": reg_num,
            "date_of_registration": reg_date.isoformat(),
            "year_established": year_established,
            "ngo_age_years": age_years,
            "operational_states": json.dumps(op_states),
            "operational_districts": json.dumps(op_districts),
            "number_of_operational_states": len(op_states),
            "number_of_operational_districts": len(op_districts),
            "sectors": json.dumps(ngo_sectors),
            "number_of_sectors": len(ngo_sectors),
            "source_count": num_raw_records,
            "retrieved_at": datetime(2026, 9, 16, 10, 0, 0).isoformat()
        })

        # ---------------------------------------------------------------------
        # 3. Dataset C: ngo_public_profile (Public Profile & Compliance Records)
        # ---------------------------------------------------------------------
        pan_provided = random.random() > 0.05
        pan_verified = pan_provided and (random.random() > 0.08)

        # Tax exemption & FCRA
        # FCRA: Applicable only if claims foreign funding or established cross-border operations
        claims_foreign = (age_years >= 3.0 and random.random() < 0.25)
        if claims_foreign:
            fcra_status = random.choice(["Valid", "Expired", "Not Found"])
        else:
            fcra_status = "Not Applicable"

        has_12a = (age_years >= 1.0 and random.random() > 0.15)
        has_80g = (has_12a and random.random() > 0.20)

        # Scale generation for financial realism (latent variable strictly for generation)
        # Small: Income ₹5L to ₹50L, Medium: ₹50L to ₹5Cr, Large: ₹5Cr to ₹50Cr
        income_bracket = random.choices(["Small", "Medium", "Large"], weights=[0.45, 0.40, 0.15])[0]
        if income_bracket == "Small":
            base_income = round(random.uniform(500000, 5000000), 2)
        elif income_bracket == "Medium":
            base_income = round(random.uniform(5000000, 50000000), 2)
        else:
            base_income = round(random.uniform(50000000, 350000000), 2)

        reported_assets = round(base_income * random.uniform(0.2, 1.8), 2)
        beneficiaries_reported = int(base_income / random.uniform(800, 2500)) if random.random() > 0.1 else None

        ngo_public_profile_rows.append({
            "ngo_id": ngo_id,
            "profile_source": "https://ngodarpan.gov.in" if random.random() > 0.2 else "NGO Website",
            "pan_provided": pan_provided,
            "pan_verified": pan_verified,
            "year_established": year_established if random.random() > 0.05 else None,
            "beneficiaries_reported": beneficiaries_reported,
            "primary_sector": primary_sector,
            "transparency_seal_status": random.choice(["Valid", "Expired", "Not Found", None]),
            "tax_exemption_type": "12AB" if has_12a else None,
            "tax_exemption_status": "Valid" if has_12a else ("Not Found" if random.random() > 0.3 else "Expired"),
            "section_80g_status": "Valid" if has_80g else ("Not Found" if random.random() > 0.3 else "Expired"),
            "fcra_status": fcra_status,
            "reported_expenditure": round(base_income * random.uniform(0.85, 1.05), 2) if random.random() > 0.15 else None,
            "reported_assets": reported_assets if random.random() > 0.20 else None,
            "profile_publication_date": (current_date - timedelta(days=random.randint(15, 300))).isoformat(),
            "source_url": f"https://eleos.org/registry/{ngo_id}",
            "verification_status": "Externally verified" if pan_verified and has_12a else "Self-reported"
        })

        # ---------------------------------------------------------------------
        # 4. Dataset D: financial_reports (Multi-Year Balance Sheets with Accounting Consistency)
        # ---------------------------------------------------------------------
        # Number of annual reports depends on age (0 for brand new, up to 5 for mature)
        if age_years < 1.0:
            num_reports = random.choice([0, 1])
        elif age_years < 3.0:
            num_reports = random.choice([1, 2])
        else:
            num_reports = random.choice([2, 3, 4, 5])

        fy_years = ["FY2025-26", "FY2024-25", "FY2023-24", "FY2022-23", "FY2021-22"]
        current_income = base_income

        for r_idx in range(num_reports):
            fy = fy_years[r_idx]
            rep_id = f"FIN_{ngo_id}_{fy}"

            # Temporal continuity: previous years differ by ±15%
            if r_idx > 0:
                yoy_factor = random.uniform(0.82, 1.18)
                current_income = round(current_income * yoy_factor, 2)

            # Income breakdown: grant_income + donation_income + other_income = total_income
            grant_pct = random.uniform(0.35, 0.75)
            don_pct = random.uniform(0.15, 1.0 - grant_pct)
            other_pct = max(0.0, 1.0 - (grant_pct + don_pct))

            grant_inc = round(current_income * grant_pct, 2)
            don_inc = round(current_income * don_pct, 2)
            other_inc = round(current_income - (grant_inc + don_inc), 2)
            tot_inc = round(grant_inc + don_inc + other_inc, 2)

            # FCRA vs NFCRA
            if fcra_status == "Valid":
                fcra_inc = round(tot_inc * random.uniform(0.15, 0.45), 2)
                nfcra_inc = round(tot_inc - fcra_inc, 2)
            else:
                fcra_inc = 0.0
                nfcra_inc = tot_inc

            # Expense generation
            # Intentional accounting anomaly on 3 specific test cases for sanity checks
            is_anomaly_ngo = (i in [42, 88, 145])
            
            # Normal distribution of expense proportions:
            # Programme: 65% - 85%, Admin: 5% - 15%, Employee: 5% - 15%, Material/Cons: 3% - 10%, Fundraising: 1% - 5%
            if is_anomaly_ngo and r_idx == 0:
                # Extreme admin overhead or severe anomaly
                admin_pct = random.uniform(0.40, 0.55)
                prog_pct = random.uniform(0.30, 0.40)
                emp_pct = random.uniform(0.05, 0.10)
                fund_pct = random.uniform(0.05, 0.10)
                other_exp_pct = max(0.0, 1.0 - (admin_pct + prog_pct + emp_pct + fund_pct))
            else:
                prog_pct = random.uniform(0.68, 0.86)
                admin_pct = random.uniform(0.05, 0.14)
                emp_pct = random.uniform(0.04, 0.10)
                fund_pct = random.uniform(0.01, 0.05)
                other_exp_pct = max(0.0, 1.0 - (prog_pct + admin_pct + emp_pct + fund_pct))

            # Total expenditure: typically 88% - 102% of income
            exp_ratio = random.uniform(0.88, 1.02)
            tot_exp = round(tot_inc * exp_ratio, 2)

            prog_exp = round(tot_exp * prog_pct, 2)
            admin_exp = round(tot_exp * admin_pct, 2)
            emp_exp = round(tot_exp * emp_pct, 2)
            fund_exp = round(tot_exp * fund_pct, 2)
            mat_exp = round(tot_exp * (other_exp_pct * 0.6), 2)
            consult_exp = round(tot_exp * (other_exp_pct * 0.3), 2)
            # Reconcile exact residual to other_expenses to strictly satisfy accounting identity
            reconciled_sum = prog_exp + admin_exp + emp_exp + fund_exp + mat_exp + consult_exp
            other_exp = round(tot_exp - reconciled_sum, 2)

            # Test 7 Sanity Check: Inject a deliberate accounting discrepancy on NGO_00077 (for Test 7)
            if i == 77 and r_idx == 0:
                tot_exp = round(tot_exp * 1.25, 2)  # Mismatch by 25%

            # Surplus or Deficit = Total Income - Total Expenditure
            surplus = round(tot_inc - tot_exp, 2)

            cash_bal = round(tot_exp * random.uniform(0.15, 0.65), 2)
            tot_assets = round(reported_assets * random.uniform(0.9, 1.1), 2)
            tot_liabilities = round(tot_assets * random.uniform(0.1, 0.4), 2)

            # Audit opinion
            if is_anomaly_ngo and r_idx == 0:
                audit_status = random.choice(["Qualified", "Adverse"])
            else:
                audit_status = random.choices(["Clean", "Qualified", "Unknown"], weights=[0.92, 0.06, 0.02])[0]

            financial_report_rows.append({
                "financial_report_id": rep_id,
                "ngo_id": ngo_id,
                "financial_year": fy,
                "document_type": "Audited Financial Statement",
                "document_source": "Public Repository" if random.random() > 0.4 else "NGO Website",
                "audit_status": audit_status,
                "auditor_name": random.choice(AUDITORS),
                "total_income": tot_inc,
                "grant_income": grant_inc,
                "donation_income": don_inc,
                "other_income": other_inc,
                "fcra_income": fcra_inc,
                "nfcra_income": nfcra_inc,
                "total_expenditure": tot_exp,
                "programme_expenses": prog_exp,
                "administrative_expenses": admin_exp,
                "fundraising_expenses": fund_exp,
                "employee_expenses": emp_exp,
                "consultancy_expenses": consult_exp,
                "material_expenses": mat_exp,
                "other_expenses": other_exp,
                "cash_and_bank_balance": cash_bal,
                "total_assets": tot_assets,
                "total_liabilities": tot_liabilities,
                "surplus_or_deficit": surplus,
                "related_party_transactions": round(tot_exp * random.uniform(0.01, 0.03), 2) if is_anomaly_ngo else 0.0,
                "source_url": f"https://eleos.org/docs/{rep_id}.pdf",
                "verification_status": "Verified" if audit_status == "Clean" else "Extracted"
            })

            # Corresponding Evidence Document (Dataset G)
            file_hash = hashlib.sha256(f"{rep_id}_{tot_inc}_{tot_exp}".encode("utf-8")).hexdigest()
            evidence_document_rows.append({
                "document_id": f"DOC_{rep_id}",
                "ngo_id": ngo_id,
                "document_type": "Audit",
                "document_name": f"Audited Financial Statement {fy}",
                "document_year": int(fy[2:6]),
                "source_url": f"https://eleos.org/docs/{rep_id}.pdf",
                "source_type": "Public Repository",
                "publication_date": (date(int(fy[2:6]), 9, 30)).isoformat(),
                "retrieved_at": datetime(2026, 9, 16, 10, 0, 0).isoformat(),
                "document_hash": file_hash,
                "extraction_status": "Success",
                "verification_status": "Verified",
                "extraction_confidence": 0.95
            })

        # ---------------------------------------------------------------------
        # 5. Dataset E: ngo_projects (Itemized Projects)
        # ---------------------------------------------------------------------
        # Projects scale reasonably with age and capacity (0 for new NGOs, 1 to 8 for older)
        if age_years < 1.0:
            num_projects = 0 if random.random() > 0.3 else 1
        elif age_years < 3.0:
            num_projects = random.randint(1, 3)
        else:
            num_projects = random.randint(2, 7)

        for p_idx in range(num_projects):
            p_id = f"PRJ_{ngo_id}_{p_idx + 1}"
            p_status = "Completed" if p_idx > 0 or random.random() > 0.3 else "Ongoing"
            start_yr = year_established + max(0, int(age_years) - p_idx - 1)
            start_d = date(min(current_date.year, start_yr), random.randint(1, 12), 1)
            dur_m = random.randint(6, 24)
            end_d = start_d + timedelta(days=dur_m * 30)

            ngo_project_rows.append({
                "project_id": p_id,
                "ngo_id": ngo_id,
                "project_name": f"{primary_sector} Initiative #{p_idx + 1} ({reg_district})",
                "project_status": p_status,
                "project_description": f"Community-based {primary_sector.lower()} support project serving rural/urban clusters.",
                "primary_sector": primary_sector,
                "secondary_sectors": json.dumps(ngo_sectors[1:]) if len(ngo_sectors) > 1 else json.dumps([]),
                "funder_name": random.choice(["CSR India Grant", "District Development Fund", "Public Donations", "State Grant", None]),
                "location_states": json.dumps([reg_state]),
                "location_districts": json.dumps([reg_district]),
                "start_date": start_d.isoformat(),
                "end_date": end_d.isoformat() if p_status == "Completed" else None,
                "duration_months": dur_m,
                "beneficiaries_reported": random.randint(200, 5000),
                "villages_covered": random.randint(2, 20),
                "milestones_reported": random.randint(3, 6),
                "milestones_completed": random.randint(2, 6) if p_status == "Completed" else random.randint(1, 3),
                "outcomes_reported": f"Successfully completed primary community training and material deployment." if p_status == "Completed" else None,
                "partnerships_reported": json.dumps(["District Administration", "Local Panchayat"]) if random.random() > 0.4 else json.dumps([]),
                "source_url": f"https://eleos.org/projects/{p_id}",
                "source_type": "Annual Report",
                "verification_status": "Self-reported"
            })

        # Add mandatory registration certificate document to Dataset G
        reg_hash = hashlib.sha256(f"REG_{ngo_id}_{reg_num}".encode("utf-8")).hexdigest()
        evidence_document_rows.append({
            "document_id": f"DOC_REG_{ngo_id}",
            "ngo_id": ngo_id,
            "document_type": "Registration",
            "document_name": f"{reg_type} Registration Certificate",
            "document_year": year_established,
            "source_url": f"https://eleos.org/docs/reg_{ngo_id}.pdf",
            "source_type": "Government",
            "publication_date": reg_date.isoformat(),
            "retrieved_at": datetime(2026, 9, 16, 10, 0, 0).isoformat(),
            "document_hash": reg_hash,
            "extraction_status": "Success",
            "verification_status": "Externally verified" if pan_verified else "Self-reported",
            "extraction_confidence": 0.98
        })

    # Convert to Pandas DataFrames
    df_registry_raw = pd.DataFrame(registry_raw_rows)
    df_ngo_master = pd.DataFrame(ngo_master_rows)
    df_ngo_public_profile = pd.DataFrame(ngo_public_profile_rows)
    df_financial_reports = pd.DataFrame(financial_report_rows)
    df_ngo_projects = pd.DataFrame(ngo_project_rows)
    df_evidence_documents = pd.DataFrame(evidence_document_rows)

    # Save to CSV
    df_registry_raw.to_csv(DATA_DIR / "ngo_registry_raw.csv", index=False)
    df_ngo_master.to_csv(DATA_DIR / "ngo_master.csv", index=False)
    df_ngo_public_profile.to_csv(DATA_DIR / "ngo_public_profile.csv", index=False)
    df_financial_reports.to_csv(DATA_DIR / "financial_reports.csv", index=False)
    df_ngo_projects.to_csv(DATA_DIR / "ngo_projects.csv", index=False)
    df_evidence_documents.to_csv(DATA_DIR / "evidence_documents.csv", index=False)

    metadata = {
        "dataset_name": "ELEOS Member 1 Reference NGO Evidence Dataset",
        "version": "reference-v1.0",
        "generation_timestamp": datetime.now().isoformat(),
        "random_seed": RANDOM_SEED,
        "total_ngos": num_ngos,
        "counts": {
            "ngo_registry_raw_records": len(df_registry_raw),
            "ngo_master_records": len(df_ngo_master),
            "ngo_public_profile_records": len(df_ngo_public_profile),
            "financial_reports_records": len(df_financial_reports),
            "ngo_projects_records": len(df_ngo_projects),
            "evidence_documents_records": len(df_evidence_documents)
        },
        "intended_use": "Validation, sensitivity analysis, pipeline evaluation, and unit testing only.",
        "real_world_validity_disclaimer": "This reference dataset does not represent real-world non-profit honesty or misconduct. Real-world validation requires genuine statutory filings from Darpan, MCA, and CBDT."
    }

    with open(DATA_DIR / "generation_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"  [SUCCESS] 6 datasets created under {DATA_DIR}")
    return {
        "registry_raw": df_registry_raw,
        "master": df_ngo_master,
        "public_profile": df_ngo_public_profile,
        "financial_reports": df_financial_reports,
        "projects": df_ngo_projects,
        "evidence_documents": df_evidence_documents
    }


generate_synthetic_data = generate_reference_data


if __name__ == "__main__":
    generate_reference_data(num_ngos=200)

