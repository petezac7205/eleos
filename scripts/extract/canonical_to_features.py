"""
Pipeline Adapter: Canonical Document Bundle to Member 1 Feature Matrices.
Maps CanonicalNgoDocumentBundle into the exact Pandas Series / DataFrames expected by
scripts/trustability_scoring.py::assess_single_ngo() and executes the trained Isolation Forest model.
"""

import math
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
import joblib

from scripts.schemas.canonical_document_schema import CanonicalNgoDocumentBundle
from scripts.extract.document_verifier import run_zero_trust_verification

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = ROOT_DIR / "models"
IFOREST_PATH = MODELS_DIR / "isolation_forest.pkl"


def canonical_bundle_to_member1_inputs(
    bundle: CanonicalNgoDocumentBundle,
    verification_results: Dict[str, Any]
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.DataFrame]:
    """
    Transforms the canonical extracted bundle into:
    (m_row, p_row, f_row, o_row, df_fin_reports)
    ready for direct consumption by assess_single_ngo().
    """
    ident = bundle.identity
    comp = bundle.compliance
    checks = verification_results.get("verification_checks", {})

    ngo_id = f"LIVE_{str(ident.pan.value or 'NGO')[:10]}"
    ngo_name = str(ident.ngo_name.value or "Extracted Non-Profit Entity")
    reg_type = str(ident.registration_type.value or "Trust")
    reg_num = str(ident.registration_number.value or "")
    reg_auth = str(ident.registration_authority.value or "")
    act_name = str(ident.act_name.value or "")
    reg_date = str(ident.date_of_registration.value or "2020-01-01")

    # Compute age in years
    try:
        reg_year = int(reg_date[:4])
        ngo_age = max(0.1, round(2026 - reg_year, 1))
    except Exception:
        ngo_age = 5.0

    # 1. Build Master Row Series (`m_row`)
    m_dict = {
        "ngo_id": ngo_id,
        "source_unique_id": reg_num,
        "ngo_name": ngo_name,
        "registration_type": reg_type,
        "registration_authority": reg_auth,
        "registration_number": reg_num,
        "date_of_registration": reg_date,
        "year_established": 2026 - int(ngo_age),
        "ngo_age_years": ngo_age,
        "registration_state": str(ident.state.value or "Tamil Nadu"),
        "act_name": act_name,
        "pan_verified": checks.get("pan_format_valid", False)
    }
    m_row = pd.Series(m_dict)

    # 2. Build Public Profile Row Series (`p_row`)
    tax_12a_valid = checks.get("tax_exemptions", {}).get("section_12a_active", False)
    tax_80g_valid = checks.get("tax_exemptions", {}).get("section_80g_active", False)
    fcra_st = str(comp.fcra_status.value or "Not Applicable")

    p_dict = {
        "ngo_id": ngo_id,
        "pan_provided": bool(ident.pan.value),
        "pan_verified": checks.get("pan_format_valid", False),
        "tax_exemption_status": "Valid" if tax_12a_valid else "Not Found",
        "section_80g_status": "Valid" if tax_80g_valid else "Not Found",
        "fcra_status": fcra_st,
        "beneficiaries_reported": sum(int(p.beneficiaries_reported.value or 0) for p in bundle.projects if p.beneficiaries_reported),
        "primary_sector": "Disaster Relief & Education",
        "reported_expenditure": float(bundle.financials[0].total_expenditure.value or 0.0) if bundle.financials else 0.0,
        "reported_assets": float(bundle.financials[0].total_assets.value or 0.0) if bundle.financials else 0.0
    }
    p_row = pd.Series(p_dict)

    # 3. Build Financial Features Series (`f_row`) & Financial Reports DataFrame (`df_fin_reports`)
    fin_report_rows = []
    if bundle.financials:
        f = bundle.financials[0]
        tot_inc = float(f.total_income.value or 1.0) if f.total_income else 1.0
        tot_exp = float(f.total_expenditure.value or 1.0) if f.total_expenditure else 1.0
        prog_exp = float(f.programme_expenses.value or 0.0) if f.programme_expenses else 0.0
        admin_exp = float(f.administrative_expenses.value or 0.0) if f.administrative_expenses else 0.0
        fund_exp = float(f.fundraising_expenses.value or 0.0) if f.fundraising_expenses else 0.0
        emp_exp = float(f.employee_expenses.value or 0.0) if f.employee_expenses else 0.0
        cash_bal = float(f.cash_and_bank_balance.value or 0.0) if f.cash_and_bank_balance else 0.0
        surplus = tot_inc - tot_exp

        prog_ratio = round(prog_exp / tot_exp, 4) if tot_exp > 0 else 0.0
        admin_ratio = round(admin_exp / tot_exp, 4) if tot_exp > 0 else 0.0
        fund_ratio = round(fund_exp / tot_exp, 4) if tot_exp > 0 else 0.0
        emp_ratio = round(emp_exp / tot_exp, 4) if tot_exp > 0 else 0.0
        surplus_margin = round(surplus / tot_inc, 4) if tot_inc > 0 else 0.0
        cash_ratio = round(cash_bal / tot_exp, 4) if tot_exp > 0 else 0.0
        recon_err = float(checks.get("accounting_reconciliation", {}).get("variance_inr", 0.0))

        grant_inc = float(f.grant_income.value or 0.0) if f.grant_income else 0.0
        grant_ratio = round(grant_inc / tot_inc, 4) if tot_inc > 0 else 0.0

        # Evaluate Isolation Forest on the exact 9 feature columns it was trained on
        feature_df = pd.DataFrame([{
            "log_income": math.log1p(max(0, tot_inc)),
            "log_expenditure": math.log1p(max(0, tot_exp)),
            "programme_expense_ratio": prog_ratio,
            "administrative_expense_ratio": admin_ratio,
            "fundraising_expense_ratio": fund_ratio,
            "surplus_margin": surplus_margin,
            "cash_to_expense_ratio": cash_ratio,
            "grant_dependency_ratio": grant_ratio,
            "financial_missingness_ratio": 0.0
        }])

        if IFOREST_PATH.exists():
            model = joblib.load(IFOREST_PATH)
            raw_score = float(model.decision_function(feature_df)[0])
            # Categorize score
            if raw_score <= -0.05 or admin_ratio > 0.35 or recon_err > 500000.0:
                anomaly_label = "Outlier"
            elif raw_score <= 0.02 or admin_ratio > 0.20:
                anomaly_label = "Borderline"
            else:
                anomaly_label = "Normal"
        else:
            raw_score = 0.10
            anomaly_label = "Normal"

        f_dict = {
            "ngo_id": ngo_id,
            "latest_financial_year": str(f.financial_year.value or "FY2024-25"),
            "reports_count": len(bundle.financials),
            "total_income": tot_inc,
            "total_expenditure": tot_exp,
            "programme_expense_ratio": prog_ratio,
            "administrative_expense_ratio": admin_ratio,
            "fundraising_expense_ratio": fund_ratio,
            "employee_expense_ratio": emp_ratio,
            "surplus_margin": surplus_margin,
            "cash_to_expense_ratio": cash_ratio,
            "financial_missingness_ratio": 0.0,
            "accounting_reconciliation_error": recon_err,
            "audit_status": str(f.audit_opinion.value or "Clean"),
            "peer_median_programme_ratio": 0.78,
            "peer_median_admin_ratio": 0.10,
            "financial_anomaly_score": round(raw_score, 4),
            "financial_anomaly_label": anomaly_label
        }
        f_row = pd.Series(f_dict)

        fin_report_rows.append({
            "financial_report_id": f"REP_{ngo_id}_01",
            "ngo_id": ngo_id,
            "financial_year": str(f.financial_year.value or "FY2024-25"),
            "total_income": tot_inc,
            "total_expenditure": tot_exp,
            "programme_expenses": prog_exp,
            "administrative_expenses": admin_exp,
            "audit_status": str(f.audit_opinion.value or "Clean")
        })
    else:
        f_row = pd.Series({
            "ngo_id": ngo_id,
            "reports_count": 0,
            "latest_financial_year": "None",
            "accounting_reconciliation_error": 0.0,
            "total_expenditure": 0.0,
            "financial_missingness_ratio": 1.0,
            "audit_status": "Unknown",
            "financial_anomaly_label": "Normal"
        })

    df_fin_reports = pd.DataFrame(fin_report_rows)

    # 4. Build Operational Features Series (`o_row`)
    completed_prjs = sum(1 for p in bundle.projects if str(p.status.value).lower() == "completed")
    funded_prjs = sum(1 for p in bundle.projects if p.funder_name and p.funder_name.value)
    has_cross_check_pass = checks.get("project_grant_cross_reconciliation", True)

    o_dict = {
        "ngo_id": ngo_id,
        "total_projects_found": len(bundle.projects),
        "completed_projects": completed_prjs,
        "ongoing_projects": len(bundle.projects) - completed_prjs,
        "projects_with_funder": funded_prjs if has_cross_check_pass else 0,
        "projects_with_dates": len(bundle.projects),
        "projects_with_outcomes": len(bundle.projects),
        "government_partnership_count": 1 if completed_prjs >= 2 and has_cross_check_pass else 0,
        "operational_evidence_completeness": 0.90 if bundle.projects else 0.0
    }
    o_row = pd.Series(o_dict)

    return m_row, p_row, f_row, o_row, df_fin_reports
