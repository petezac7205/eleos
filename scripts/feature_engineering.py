"""
ELEOS — Member 1: Financial & Operational Feature Engineering
Generates:
1. financial_features.csv (Dataset: engineered ratios, multi-year trends, missingness)
2. operational_features.csv (Dataset: documented project track record, evidence completeness)
3. Implements Peer-Group Construction with explicit fallback hierarchy and minimum group size.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "synthetic"
DATA_DIR = ROOT_DIR / "data" / "reference"

# Minimum peer group size to avoid small-sample distortions
MIN_PEER_GROUP_SIZE = 10


def categorize_income_scale(income: Optional[float]) -> str:
    """Categorizes annual income into operational scale brackets."""
    if pd.isna(income) or income is None or income <= 0:
        return "Unknown"
    if income < 5000000:       # < ₹50 Lakhs
        return "Small"
    elif income < 50000000:    # ₹50 Lakhs - ₹5 Crores
        return "Medium"
    else:                      # > ₹5 Crores
        return "Large"


def safe_div(num: Optional[float], den: Optional[float], default: Optional[float] = None) -> Optional[float]:
    """Safe division guarding against division by zero and None values."""
    if num is None or den is None or pd.isna(num) or pd.isna(den):
        return default
    if den == 0:
        return default
    return round(float(num) / float(den), 4)


def build_financial_features(df_master: pd.DataFrame, df_fin: pd.DataFrame, df_profile: pd.DataFrame) -> pd.DataFrame:
    """
    Computes standard financial ratios, YoY trends, and missingness metrics per NGO.
    Uses the latest available financial report while incorporating multi-year continuity.
    """
    records = []

    # Sort by ngo_id and financial_year (descending so FY2025-26 comes first)
    df_sorted = df_fin.sort_values(by=["ngo_id", "financial_year"], ascending=[True, False])

    for ngo_id in df_master["ngo_id"].unique():
        ngo_reports = df_sorted[df_sorted["ngo_id"] == ngo_id]
        profile_row = df_profile[df_profile["ngo_id"] == ngo_id].iloc[0] if len(df_profile[df_profile["ngo_id"] == ngo_id]) > 0 else None

        if len(ngo_reports) == 0:
            # NGO with 0 financial reports (e.g. brand new NGO)
            records.append({
                "ngo_id": ngo_id,
                "latest_financial_year": None,
                "reports_count": 0,
                "total_income": None,
                "total_expenditure": None,
                "income_scale": "Unknown",
                "programme_expense_ratio": None,
                "administrative_expense_ratio": None,
                "fundraising_expense_ratio": None,
                "employee_expense_ratio": None,
                "surplus_margin": None,
                "year_over_year_income_growth": None,
                "year_over_year_expense_growth": None,
                "cash_to_expense_ratio": None,
                "grant_dependency_ratio": None,
                "fcra_dependency_ratio": None,
                "asset_to_income_ratio": None,
                "financial_missingness_ratio": 1.0,
                "accounting_reconciliation_error": 0.0,
                "audit_status": "No Reports Available"
            })
            continue

        # Latest report (index 0 in sorted group)
        latest = ngo_reports.iloc[0]
        tot_inc = latest["total_income"]
        tot_exp = latest["total_expenditure"]
        inc_scale = categorize_income_scale(tot_inc)

        # Expense breakdown ratios
        prog_ratio = safe_div(latest["programme_expenses"], tot_exp)
        admin_ratio = safe_div(latest["administrative_expenses"], tot_exp)
        fund_ratio = safe_div(latest["fundraising_expenses"], tot_exp)
        emp_ratio = safe_div(latest["employee_expenses"], tot_exp)
        surplus_margin = safe_div(latest["surplus_or_deficit"], tot_inc)

        # Cash & Asset ratios
        cash_ratio = safe_div(latest["cash_and_bank_balance"], tot_exp)
        asset_ratio = safe_div(latest["total_assets"], tot_inc)
        grant_dep = safe_div(latest["grant_income"], tot_inc)
        fcra_dep = safe_div(latest["fcra_income"], tot_inc)

        # YoY Growth rates if >= 2 reports
        yoy_inc_growth = None
        yoy_exp_growth = None
        if len(ngo_reports) >= 2:
            prev = ngo_reports.iloc[1]
            if prev["total_income"] and prev["total_income"] > 0:
                yoy_inc_growth = round((float(tot_inc) - float(prev["total_income"])) / float(prev["total_income"]), 4)
            if prev["total_expenditure"] and prev["total_expenditure"] > 0:
                yoy_exp_growth = round((float(tot_exp) - float(prev["total_expenditure"])) / float(prev["total_expenditure"]), 4)

        # Financial missingness: fraction of null expected financial fields
        core_fin_fields = [
            latest["total_income"], latest["total_expenditure"], latest["programme_expenses"],
            latest["administrative_expenses"], latest["cash_and_bank_balance"], latest["total_assets"],
            latest["total_liabilities"], latest["surplus_or_deficit"]
        ]
        missing_count = sum(1 for f in core_fin_fields if pd.isna(f) or f is None)
        fin_missingness = round(missing_count / len(core_fin_fields), 4)

        # Accounting reconciliation error: |total_expenditure - sum(items)|
        items_sum = sum(
            float(latest[col]) for col in [
                "programme_expenses", "administrative_expenses", "fundraising_expenses",
                "employee_expenses", "consultancy_expenses", "material_expenses", "other_expenses"
            ] if not pd.isna(latest[col]) and latest[col] is not None
        )
        recon_err = round(abs(float(tot_exp) - items_sum), 2) if tot_exp else 0.0

        records.append({
            "ngo_id": ngo_id,
            "latest_financial_year": latest["financial_year"],
            "reports_count": len(ngo_reports),
            "total_income": tot_inc,
            "total_expenditure": tot_exp,
            "income_scale": inc_scale,
            "programme_expense_ratio": prog_ratio,
            "administrative_expense_ratio": admin_ratio,
            "fundraising_expense_ratio": fund_ratio,
            "employee_expense_ratio": emp_ratio,
            "surplus_margin": surplus_margin,
            "year_over_year_income_growth": yoy_inc_growth,
            "year_over_year_expense_growth": yoy_exp_growth,
            "cash_to_expense_ratio": cash_ratio,
            "grant_dependency_ratio": grant_dep,
            "fcra_dependency_ratio": fcra_dep,
            "asset_to_income_ratio": asset_ratio,
            "financial_missingness_ratio": fin_missingness,
            "accounting_reconciliation_error": recon_err,
            "audit_status": latest.get("audit_status", "Clean")
        })

    return pd.DataFrame(records)


def build_operational_features(df_master: pd.DataFrame, df_projects: pd.DataFrame) -> pd.DataFrame:
    """
    Computes operational features per NGO based on publicly documented projects.
    Beneficiary counts are descriptive, not an automatic trust score booster.
    """
    records = []

    for ngo_id in df_master["ngo_id"].unique():
        prjs = df_projects[df_projects["ngo_id"] == ngo_id]
        total_found = len(prjs)

        if total_found == 0:
            records.append({
                "ngo_id": ngo_id,
                "total_projects_found": 0,
                "completed_projects": 0,
                "ongoing_projects": 0,
                "planned_projects": 0,
                "total_project_locations": 0,
                "total_beneficiaries_reported": 0,
                "projects_with_funder": 0,
                "projects_with_dates": 0,
                "projects_with_outcomes": 0,
                "projects_with_milestones": 0,
                "government_partnership_count": 0,
                "operational_evidence_completeness": 0.0
            })
            continue

        completed = sum(1 for _, p in prjs.iterrows() if p["project_status"] == "Completed")
        ongoing = sum(1 for _, p in prjs.iterrows() if p["project_status"] == "Ongoing")
        planned = sum(1 for _, p in prjs.iterrows() if p["project_status"] == "Planned")

        tot_beneficiaries = sum(int(p["beneficiaries_reported"]) for _, p in prjs.iterrows() if not pd.isna(p["beneficiaries_reported"]))
        with_funder = sum(1 for _, p in prjs.iterrows() if not pd.isna(p["funder_name"]) and p["funder_name"])
        with_dates = sum(1 for _, p in prjs.iterrows() if not pd.isna(p["start_date"]))
        with_outcomes = sum(1 for _, p in prjs.iterrows() if not pd.isna(p["outcomes_reported"]) and p["outcomes_reported"])
        with_milestones = sum(1 for _, p in prjs.iterrows() if not pd.isna(p["milestones_completed"]) and p["milestones_completed"] > 0)

        # Count reported government partnerships
        gov_partnerships = 0
        for _, p in prjs.iterrows():
            parts_str = p.get("partnerships_reported", "[]")
            if isinstance(parts_str, str) and ("District" in parts_str or "Panchayat" in parts_str or "Government" in parts_str):
                gov_partnerships += 1

        # Evidence completeness score for operations (0.0 to 1.0)
        metadata_checks = [
            with_dates / total_found,
            with_funder / total_found,
            with_milestones / total_found,
            with_outcomes / max(1, completed)
        ]
        op_completeness = round(sum(metadata_checks) / len(metadata_checks), 4)

        records.append({
            "ngo_id": ngo_id,
            "total_projects_found": total_found,
            "completed_projects": completed,
            "ongoing_projects": ongoing,
            "planned_projects": planned,
            "total_project_locations": total_found,
            "total_beneficiaries_reported": tot_beneficiaries,
            "projects_with_funder": with_funder,
            "projects_with_dates": with_dates,
            "projects_with_outcomes": with_outcomes,
            "projects_with_milestones": with_milestones,
            "government_partnership_count": gov_partnerships,
            "operational_evidence_completeness": op_completeness
        })

    return pd.DataFrame(records)


def assign_peer_groups(df_fin_feats: pd.DataFrame, df_profile: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns peer groups based on (primary_sector, income_scale).
    Enforces MIN_PEER_GROUP_SIZE = 10 with clear fallback behavior:
    1. Primary: (sector, income_scale) if count >= MIN_PEER_GROUP_SIZE
    2. Fallback 1: (sector) across all income scales if count >= MIN_PEER_GROUP_SIZE
    3. Fallback 2: 'All_NGOs' baseline reference population if still < MIN_PEER_GROUP_SIZE
    """
    df = df_fin_feats.merge(df_profile[["ngo_id", "primary_sector"]], on="ngo_id", how="left")
    
    # Calculate group sizes
    specific_counts = df.groupby(["primary_sector", "income_scale"])["ngo_id"].transform("count")
    sector_counts = df.groupby("primary_sector")["ngo_id"].transform("count")

    peer_group_names = []
    fallback_levels = []
    peer_group_sizes = []

    for idx, row in df.iterrows():
        sec = row["primary_sector"]
        inc = row["income_scale"]
        s_cnt = specific_counts.iloc[idx]
        sec_cnt = sector_counts.iloc[idx]

        if s_cnt >= MIN_PEER_GROUP_SIZE:
            peer_group_names.append(f"{sec}_{inc}")
            fallback_levels.append("specific")
            peer_group_sizes.append(int(s_cnt))
        elif sec_cnt >= MIN_PEER_GROUP_SIZE:
            peer_group_names.append(f"{sec}_Broad")
            fallback_levels.append("sector_broad")
            peer_group_sizes.append(int(sec_cnt))
        else:
            peer_group_names.append("All_NGOs_National")
            fallback_levels.append("national_broad")
            peer_group_sizes.append(len(df))

    df["peer_group"] = peer_group_names
    df["peer_group_fallback_level"] = fallback_levels
    df["peer_group_size"] = peer_group_sizes

    # Calculate peer group medians for programme and admin expense ratios
    peer_medians = df.groupby("peer_group")[["programme_expense_ratio", "administrative_expense_ratio"]].transform("median")
    df["peer_median_programme_ratio"] = peer_medians["programme_expense_ratio"].round(4)
    df["peer_median_admin_ratio"] = peer_medians["administrative_expense_ratio"].round(4)

    return df


def run_feature_engineering() -> Dict[str, pd.DataFrame]:
    print("[3/7] Running feature engineering & peer-group indexing...")

    df_master = pd.read_csv(DATA_DIR / "ngo_master.csv")
    df_fin = pd.read_csv(DATA_DIR / "financial_reports.csv")
    df_profile = pd.read_csv(DATA_DIR / "ngo_public_profile.csv")
    df_projects = pd.read_csv(DATA_DIR / "ngo_projects.csv")

    df_fin_feats = build_financial_features(df_master, df_fin, df_profile)
    df_fin_feats = assign_peer_groups(df_fin_feats, df_profile)
    df_op_feats = build_operational_features(df_master, df_projects)

    df_fin_feats.to_csv(DATA_DIR / "financial_features.csv", index=False)
    df_op_feats.to_csv(DATA_DIR / "operational_features.csv", index=False)

    print(f"  [SUCCESS] Financial features ({len(df_fin_feats)} rows) and Operational features ({len(df_op_feats)} rows) generated.")
    return {"financial_features": df_fin_feats, "operational_features": df_op_feats}


if __name__ == "__main__":
    run_feature_engineering()

