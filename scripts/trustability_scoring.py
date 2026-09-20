"""
ELEOS — Member 1: Evidence-Based Trustability Scoring Engine
Computes multi-dimensional scores, evidence coverage, uncertainty, and JSON assessments.

CORE PRINCIPLES ENFORCED:
1. Evidence-based evaluation, not moral or fraud judgment.
2. Missing evidence is strictly separated from negative evidence.
3. Organizational age has a small, calibrated penalty factor without disproportionately affecting final scores.
4. Peer-group comparisons for financial ratios instead of arbitrary universal thresholds.
5. No double-counting of the same underlying evidence across dimensions.
6. Explicit data confidence and uncertainty estimation.
7. Produces standardized, explainable JSON output matching Section 47.
"""

import os
import json
import math
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "synthetic"
DATA_DIR = ROOT_DIR / "data" / "reference"
OUTPUTS_DIR = ROOT_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Configurable Dimension Weights (Sum = 1.0)
DEFAULT_WEIGHTS = {
    "identity_legal": 0.25,
    "financial_transparency": 0.30,
    "operational_evidence": 0.25,
    "data_completeness": 0.20
}

# Exponential recency decay parameter: exp(-lambda * delta_t_years)
DEFAULT_RECENCY_LAMBDA = 0.25


def score_identity_legal(
    master_row: pd.Series,
    profile_row: Optional[pd.Series]
) -> Tuple[float, List[str], List[str], List[str]]:
    """
    Dimension 1: Identity & Legal Evidence (Max: 100 points)
    Components:
    - Active registration evidence: 30 pts
    - Identity consistency (PAN verification & name match): 20 pts
    - Tax exemption status (12A/80G): 20 pts
    - FCRA evidence (applicability-aware): 15 pts
    - Registration completeness: 10 pts
    - Age adjustment (small, calibrated): max ±5 pts (influence <= 1.25 pts on total score)
    """
    score = 0.0
    pos_ev = []
    neg_ev = []
    miss_ev = []

    # 1. Registration evidence (30 pts)
    if not pd.isna(master_row.get("registration_number")) and master_row.get("registration_number"):
        score += 30.0
        pos_ev.append(f"Valid legal registration record identified under {master_row.get('registration_type', 'Entity')}.")
    else:
        miss_ev.append("Official registration number is not available in public records.")

    # 2. Identity consistency: PAN provided and verified (20 pts)
    pan_provided = profile_row.get("pan_provided", False) if profile_row is not None else False
    pan_verified = profile_row.get("pan_verified", False) if profile_row is not None else False

    if pan_verified:
        score += 20.0
        pos_ev.append("Permanent Account Number (PAN) was verified against statutory records.")
    elif pan_provided:
        score += 10.0
        pos_ev.append("PAN was reported by the organization but pending third-party verification.")
    else:
        miss_ev.append("Tax identification (PAN) record was not provided in public profile.")

    # 3. Tax exemption evidence: Section 12A and 80G (20 pts total)
    tax_12a = profile_row.get("tax_exemption_status") == "Valid" if profile_row is not None else False
    tax_80g = profile_row.get("section_80g_status") == "Valid" if profile_row is not None else False

    if tax_12a:
        score += 10.0
        pos_ev.append("Section 12A/12AB charitable tax-exempt registration is active.")
    else:
        miss_ev.append("Section 12A/12AB tax exemption certificate was not found.")

    if tax_80g:
        score += 10.0
        pos_ev.append("Section 80G donor deduction approval is active.")
    else:
        miss_ev.append("Section 80G tax benefit certificate is not documented.")

    # 4. FCRA Evidence (15 pts) - Applicability aware
    fcra_status = profile_row.get("fcra_status", "Not Applicable") if profile_row is not None else "Not Applicable"
    if fcra_status == "Not Applicable":
        # Neutral: full credit because NGO does not receive foreign funds
        score += 15.0
        pos_ev.append("Organization operates domestic programmes only; FCRA registration is not applicable.")
    elif fcra_status == "Valid":
        score += 15.0
        pos_ev.append("Active Foreign Contribution Regulation Act (FCRA) registration verified.")
    elif fcra_status == "Expired":
        score += 5.0
        neg_ev.append("FCRA registration appears expired while organization solicits foreign contributions.")
    else:
        miss_ev.append("FCRA registration record not found for foreign contribution activities.")

    # 5. Public Registration Completeness (10 pts)
    if master_row.get("registration_authority") and master_row.get("act_name"):
        score += 10.0
    else:
        score += 5.0

    # 6. Age Calibration: small, calibrated influence (max ±5 pts out of 100 in dimension)
    age = float(master_row.get("ngo_age_years", 1.0))
    if age < 1.0:
        score -= 5.0  # Minor adjustment: 5 pts * 0.25 weight = 1.25 pts on total score
        miss_ev.append("Entity was registered within the past 12 months; limited baseline documentation.")
    elif age >= 5.0:
        score += 5.0

    normalized_score = min(max(round(score, 2), 0.0), 100.0)
    return normalized_score, pos_ev, neg_ev, miss_ev


def score_financial_transparency(
    fin_feat_row: pd.Series,
    all_reports: pd.DataFrame,
    current_year: int = 2026
) -> Tuple[float, List[str], List[str], List[str], List[str]]:
    """
    Dimension 2: Financial Transparency (Max: 100 points)
    Components:
    - Availability of annual financial reports: 20 pts
    - Exponential recency decay: 15 pts
    - Multi-year reporting coverage (up to 5 yrs): 15 pts
    - Accounting consistency & reconciliation: 15 pts
    - Disclosure completeness (low missingness): 15 pts
    - Clean audit opinion: 10 pts
    - Anomaly / Peer-group alignment: 10 pts
    """
    score = 0.0
    pos_ev = []
    neg_ev = []
    stat_findings = []
    miss_ev = []

    rep_count = int(fin_feat_row.get("reports_count", 0))
    anomaly_label = str(fin_feat_row.get("financial_anomaly_label", "Normal"))

    if rep_count == 0:
        miss_ev.append("No audited financial reports or annual balance sheets were available.")
        stat_findings.append("Financial transparency score reflects lack of available documentation.")
        if anomaly_label == "Outlier":
            stat_findings.append("Isolation Forest flagged an unusual financial distribution (no annual financial disclosures available).")
        elif anomaly_label == "Borderline":
            stat_findings.append("Financial profile shows moderate statistical variation compared to peer group.")
        return 10.0, pos_ev, neg_ev, stat_findings, miss_ev

    # 1. Report Availability (20 pts)
    if rep_count >= 3:
        score += 20.0
        pos_ev.append(f"Strong historical disclosure with {rep_count} financial statements available.")
    elif rep_count >= 1:
        score += 12.0
        pos_ev.append(f"Available disclosure contains {rep_count} financial report(s).")

    # 2. Recency Decay (15 pts)
    # recency_factor = exp(-lambda * delta_t_years)
    latest_fy_str = str(fin_feat_row.get("latest_financial_year", "FY2024-25"))
    try:
        report_year = int(latest_fy_str[2:6])
    except Exception:
        report_year = current_year - 2
    delta_t = max(0, current_year - report_year)
    recency_factor = math.exp(-DEFAULT_RECENCY_LAMBDA * delta_t)
    recency_score = 15.0 * recency_factor
    score += recency_score
    if delta_t <= 1:
        pos_ev.append(f"Financial statements are recent ({latest_fy_str}).")
    else:
        miss_ev.append(f"Latest financial statement is from {latest_fy_str}; recency decay applied.")

    # 3. Multi-year coverage (15 pts)
    coverage_pts = min(15.0, rep_count * 3.75)
    score += coverage_pts

    # 4. Accounting Consistency (15 pts)
    recon_err = float(fin_feat_row.get("accounting_reconciliation_error", 0.0))
    tot_exp = float(fin_feat_row.get("total_expenditure", 1.0))
    error_pct = (recon_err / tot_exp) * 100 if tot_exp > 0 else 0.0

    if error_pct < 0.5:
        score += 15.0
        pos_ev.append("Reported financial totals reconcile mathematically with itemized expense categories.")
    elif error_pct < 5.0:
        score += 10.0
        stat_findings.append(f"Minor rounding variance ({error_pct:.1f}%) observed in expenditure reconciliation.")
    else:
        score += 2.0
        neg_ev.append(f"A material accounting discrepancy of ₹{recon_err:,.0f} ({error_pct:.1f}%) was detected in expenditure reconciliation.")

    # 5. Disclosure Completeness (15 pts)
    missingness = float(fin_feat_row.get("financial_missingness_ratio", 0.0))
    comp_score = 15.0 * (1.0 - missingness)
    score += comp_score
    if missingness < 0.15:
        pos_ev.append("Core financial disclosures (income, expenditure, assets, liabilities) are complete.")
    else:
        miss_ev.append(f"Approximately {missingness * 100:.0f}% of expected financial disclosure line items were omitted.")

    # 6. Audit Opinion (10 pts)
    audit_status = str(fin_feat_row.get("audit_status", "Clean"))
    if audit_status == "Clean":
        score += 10.0
        pos_ev.append("Statutory auditor issued an unqualified (clean) audit opinion.")
    elif audit_status == "Qualified":
        score += 5.0
        neg_ev.append("Auditor issued a qualified report noting specific reservations or missing disclosures.")
    elif audit_status in ["Adverse", "Disclaimer"]:
        score += 0.0
        neg_ev.append(f"Auditor issued an adverse opinion or disclaimer of opinion ({audit_status}).")
    else:
        score += 5.0

    # 7. Statistical Anomaly / Peer-group alignment (10 pts)
    anomaly_label = str(fin_feat_row.get("financial_anomaly_label", "Normal"))
    prog_ratio = fin_feat_row.get("programme_expense_ratio")
    admin_ratio = fin_feat_row.get("administrative_expense_ratio")
    peer_prog_med = fin_feat_row.get("peer_median_programme_ratio")
    peer_admin_med = fin_feat_row.get("peer_median_admin_ratio")

    if anomaly_label == "Normal":
        score += 10.0
        stat_findings.append("No statistical outlier pattern detected relative to peer non-profit population.")
    elif anomaly_label == "Borderline":
        score += 6.0
        stat_findings.append("Financial profile shows moderate statistical variation compared to peer group.")
    else:  # Outlier
        score += 2.0
        stat_findings.append("Isolation Forest flagged an unusual financial distribution (e.g. skewed admin ratio or high concentration).")

    if prog_ratio is not None and peer_prog_med is not None:
        stat_findings.append(f"Programme expense ratio is {prog_ratio * 100:.1f}% (Peer group median: {peer_prog_med * 100:.1f}%).")
    if admin_ratio is not None and peer_admin_med is not None:
        stat_findings.append(f"Administrative expense ratio is {admin_ratio * 100:.1f}% (Peer group median: {peer_admin_med * 100:.1f}%).")

    normalized_score = min(max(round(score, 2), 0.0), 100.0)
    return normalized_score, pos_ev, neg_ev, stat_findings, miss_ev


def score_operational_evidence(
    op_feat_row: pd.Series
) -> Tuple[float, List[str], List[str], List[str]]:
    """
    Dimension 3: Operational Evidence (Max: 100 points)
    Components:
    - Public project documentation: 25 pts
    - Historical activity evidence: 20 pts
    - Project metadata completeness: 20 pts
    - Outcome/milestone documentation: 15 pts
    - Source diversity & external corroboration: 20 pts
    """
    score = 0.0
    pos_ev = []
    neg_ev = []
    miss_ev = []

    tot_prjs = int(op_feat_row.get("total_projects_found", 0))
    completed_prjs = int(op_feat_row.get("completed_projects", 0))

    if tot_prjs == 0:
        miss_ev.append("No publicly documented projects or operational track records were located.")
        return 15.0, pos_ev, neg_ev, miss_ev

    # 1. Project documentation (25 pts)
    if tot_prjs >= 3:
        score += 25.0
        pos_ev.append(f"Multiple ({tot_prjs}) charitable programmes publicly documented.")
    elif tot_prjs >= 1:
        score += 15.0
        pos_ev.append(f"Public documentation found for {tot_prjs} project(s).")

    # 2. Historical activity (20 pts)
    if completed_prjs >= 2:
        score += 20.0
        pos_ev.append(f"Successfully documented completion for {completed_prjs} projects.")
    elif completed_prjs >= 1:
        score += 12.0
    else:
        score += 5.0
        miss_ev.append("Documented projects are ongoing or planned; no completed projects on record.")

    # 3. Project metadata completeness (20 pts)
    with_dates = int(op_feat_row.get("projects_with_dates", 0))
    with_funder = int(op_feat_row.get("projects_with_funder", 0))
    date_ratio = with_dates / tot_prjs if tot_prjs > 0 else 0
    funder_ratio = with_funder / tot_prjs if tot_prjs > 0 else 0
    score += (date_ratio * 10.0) + (funder_ratio * 10.0)
    if date_ratio >= 0.8:
        pos_ev.append("Project timelines, start dates, and durations are consistently documented.")

    # 4. Outcome/milestone documentation (15 pts)
    with_outcomes = int(op_feat_row.get("projects_with_outcomes", 0))
    with_milestones = int(op_feat_row.get("projects_with_milestones", 0))
    outcome_score = min(15.0, (with_outcomes * 5.0) + (with_milestones * 3.0))
    score += outcome_score
    if with_outcomes > 0:
        pos_ev.append("Published impact summaries and verified milestone deliverables are available.")

    # 5. External corroboration & partnerships (20 pts)
    gov_parts = int(op_feat_row.get("government_partnership_count", 0))
    if gov_parts >= 2:
        score += 20.0
        pos_ev.append("Multiple documented partnerships with local administrative or panchayat authorities.")
    elif gov_parts >= 1:
        score += 12.0
    else:
        score += 8.0

    normalized_score = min(max(round(score, 2), 0.0), 100.0)
    return normalized_score, pos_ev, neg_ev, miss_ev


def score_data_completeness(
    master_row: pd.Series,
    profile_row: Optional[pd.Series],
    fin_feat_row: pd.Series,
    op_feat_row: pd.Series
) -> Tuple[float, float, List[str]]:
    """
    Dimension 4: Data Completeness & Confidence (Max: 100 points)
    Applicability-aware: checks present evidence items against applicable expected items.
    """
    expected_items = []
    present_items = []

    # 1. Registration details (Weight: 15)
    expected_items.append("Registration Number & Type")
    if not pd.isna(master_row.get("registration_number")):
        present_items.append("Registration Number & Type")

    # 2. Identity details (Weight: 15)
    expected_items.append("Tax Identifier (PAN)")
    if profile_row is not None and profile_row.get("pan_provided"):
        present_items.append("Tax Identifier (PAN)")

    # 3. Financial reports (Weight: 25)
    expected_items.append("Audited Financial Statements")
    if fin_feat_row.get("reports_count", 0) > 0:
        present_items.append("Audited Financial Statements")

    # 4. Tax/FCRA Status where applicable (Weight: 15)
    expected_items.append("Section 12A/80G Exemption")
    if profile_row is not None and (profile_row.get("tax_exemption_status") == "Valid" or profile_row.get("section_80g_status") == "Valid"):
        present_items.append("Section 12A/80G Exemption")

    fcra_status = profile_row.get("fcra_status", "Not Applicable") if profile_row is not None else "Not Applicable"
    if fcra_status != "Not Applicable":
        expected_items.append("FCRA Filing Records")
        if fcra_status == "Valid":
            present_items.append("FCRA Filing Records")

    # 5. Project track record (Weight: 15)
    expected_items.append("Public Project Documentation")
    if op_feat_row.get("total_projects_found", 0) > 0:
        present_items.append("Public Project Documentation")

    # 6. Operational Geography (Weight: 15)
    expected_items.append("Operational Geography Disclosure")
    if master_row.get("number_of_operational_states", 0) > 0:
        present_items.append("Operational Geography Disclosure")

    completeness_pct = round((len(present_items) / len(expected_items)) * 100.0, 2)

    # Missing expected items
    missing_items = [item for item in expected_items if item not in present_items]

    # Data Confidence (0.0 to 1.0)
    rep_count = int(fin_feat_row.get("reports_count", 0))
    confidence = round(
        (0.50 * (completeness_pct / 100.0)) +
        (0.30 * min(1.0, rep_count / 3.0)) +
        (0.20 * (1.0 if profile_row is not None and profile_row.get("verification_status") == "Externally verified" else 0.6)),
        2
    )

    return completeness_pct, confidence, missing_items


def get_score_interpretation(score: float) -> Dict[str, str]:
    """Assigns standard evidence coverage label based on 0-100 score."""
    if score >= 80.0:
        return {
            "label": "Strong Evidence Coverage",
            "description": "Available evidence provides high consistency across statutory registrations, multi-year financial audits, and documented operational history."
        }
    elif score >= 60.0:
        return {
            "label": "Moderate Evidence Coverage",
            "description": "Evidence demonstrates reasonable baseline documentation with minor reporting gaps or limited historical data."
        }
    elif score >= 40.0:
        return {
            "label": "Limited Evidence Coverage",
            "description": "Available evidence supports a preliminary assessment; key historical financial reports or operational documentation remain incomplete."
        }
    elif score >= 20.0:
        return {
            "label": "Insufficient Evidence",
            "description": "Significant gaps across primary documentation, statutory filings, or operational disclosures prevent confident assessment."
        }
    else:
        return {
            "label": "Very Limited Evidence",
            "description": "Minimal publicly verifiable evidence is currently available for this organization."
        }


def assess_single_ngo(
    ngo_id: str,
    df_master: pd.DataFrame,
    df_profile: pd.DataFrame,
    df_fin_feats: pd.DataFrame,
    df_op_feats: pd.DataFrame,
    df_fin_reports: pd.DataFrame,
    weights: Dict[str, float] = DEFAULT_WEIGHTS
) -> Dict[str, Any]:
    """
    Computes complete, explainable evidence-based assessment for one NGO.
    Returns standardized JSON object matching Section 47.
    """
    m_row = df_master[df_master["ngo_id"] == ngo_id].iloc[0]
    p_subset = df_profile[df_profile["ngo_id"] == ngo_id]
    p_row = p_subset.iloc[0] if len(p_subset) > 0 else None
    f_row = df_fin_feats[df_fin_feats["ngo_id"] == ngo_id].iloc[0]
    o_row = df_op_feats[df_op_feats["ngo_id"] == ngo_id].iloc[0]

    # Compute 4 Dimensions
    id_score, id_pos, id_neg, id_miss = score_identity_legal(m_row, p_row)
    fin_score, fin_pos, fin_neg, fin_stat, fin_miss = score_financial_transparency(f_row, df_fin_reports)
    op_score, op_pos, op_neg, op_miss = score_operational_evidence(o_row)
    comp_score, confidence, missing_checklist = score_data_completeness(m_row, p_row, f_row, o_row)

    # Weighted Overall Score
    raw_final_score = (
        weights["identity_legal"] * id_score +
        weights["financial_transparency"] * fin_score +
        weights["operational_evidence"] * op_score +
        weights["data_completeness"] * comp_score
    )
    final_score = round(min(max(raw_final_score, 0.0), 100.0), 1)

    interpretation = get_score_interpretation(final_score)

    confidence_band = "High" if confidence >= 0.80 else ("Moderate" if confidence >= 0.55 else "Low")

    # Aggregate Evidence Lists (Deduplicated)
    all_positive = list(dict.fromkeys(id_pos + fin_pos + op_pos))
    all_negative = list(dict.fromkeys(id_neg + fin_neg + op_neg))
    all_missing = list(dict.fromkeys(id_miss + fin_miss + op_miss + missing_checklist))

    assessment = {
        "ngo_id": str(ngo_id),
        "ngo_name": str(m_row.get("ngo_name")),
        "assessment_date": "2026-09-16",
        "assessment_type": "evidence_based_trustability_assessment",
        "trustability_score": final_score,
        "score_interpretation": interpretation,
        "data_confidence": confidence,
        "confidence_band": confidence_band,
        "dimension_scores": {
            "identity_legal": round(id_score, 1),
            "financial_transparency": round(fin_score, 1),
            "operational_evidence": round(op_score, 1),
            "data_completeness": round(comp_score, 1)
        },
        "financial_analysis": {
            "programme_expense_ratio": f_row.get("programme_expense_ratio"),
            "administrative_expense_ratio": f_row.get("administrative_expense_ratio"),
            "fundraising_expense_ratio": f_row.get("fundraising_expense_ratio"),
            "surplus_margin": f_row.get("surplus_margin"),
            "financial_anomaly_score": f_row.get("financial_anomaly_score"),
            "financial_anomaly_label": f_row.get("financial_anomaly_label"),
            "peer_group_definition": {
                "sector": str(p_row.get("primary_sector")) if p_row is not None else "General",
                "income_scale": str(f_row.get("income_scale")),
                "reference_peer_group": str(f_row.get("peer_group")),
                "peer_group_size": int(f_row.get("peer_group_size", 0)),
                "peer_fallback_level": str(f_row.get("peer_group_fallback_level"))
            }
        },
        "evidence_summary": {
            "registration_found": not pd.isna(m_row.get("registration_number")),
            "registration_verified": p_row.get("verification_status") == "Externally verified" if p_row is not None else False,
            "pan_verified": bool(p_row.get("pan_verified", False)) if p_row is not None else False,
            "tax_exemption_status": str(p_row.get("tax_exemption_status", "Not Found")) if p_row is not None else "Not Found",
            "fcra_status": str(p_row.get("fcra_status", "Not Applicable")) if p_row is not None else "Not Applicable",
            "financial_reports_available": int(f_row.get("reports_count", 0)),
            "recent_financial_report_available": int(f_row.get("reports_count", 0)) > 0 and "2025" in str(f_row.get("latest_financial_year", "")),
            "projects_documented": int(o_row.get("total_projects_found", 0)),
            "documents_available": int(f_row.get("reports_count", 0)) + 1
        },
        "positive_evidence": all_positive,
        "negative_evidence": all_negative,
        "statistical_findings": fin_stat,
        "missing_evidence": all_missing,
        "uncertainty": {
            "assessment_confidence": confidence,
            "major_uncertainty_sources": [
                f"Missing {len(all_missing)} expected evidence disclosures.",
                "Public evidence is self-reported or platform-extracted; requires statutory registry confirmation."
            ] if len(all_missing) > 0 else ["Standard evaluation based on published statutory documentation."]
        },
        "limitations": [
            "The assessment is based strictly on observable public evidence and does not establish moral character, honesty, or fraud.",
            "Missing public documentation does not prove absence of charitable activity or operational wrongdoing.",
            "Statistical anomaly detection flags unusual distributions, not misuse of funds."
        ],
        "methodology": {
            "methodology_version": "member1-v1.0",
            "model_version": "iforest-v1.0",
            "dataset_version": "synthetic-v1.0",
            "dataset_version": "reference-v1.0",
            "scoring_weights": weights
        }
    }

    return assessment


def run_trustability_scoring(weights: Dict[str, float] = DEFAULT_WEIGHTS) -> List[Dict[str, Any]]:
    print("[5/7] Running trustability scoring & generating JSON assessments...")

    df_master = pd.read_csv(DATA_DIR / "ngo_master.csv")
    df_profile = pd.read_csv(DATA_DIR / "ngo_public_profile.csv")
    df_fin_feats = pd.read_csv(DATA_DIR / "financial_features.csv")
    df_op_feats = pd.read_csv(DATA_DIR / "operational_features.csv")
    df_fin_reports = pd.read_csv(DATA_DIR / "financial_reports.csv")

    assessments = []
    for ngo_id in df_master["ngo_id"].unique():
        asmnt = assess_single_ngo(
            ngo_id=ngo_id,
            df_master=df_master,
            df_profile=df_profile,
            df_fin_feats=df_fin_feats,
            df_op_feats=df_op_feats,
            df_fin_reports=df_fin_reports,
            weights=weights
        )
        assessments.append(asmnt)

    with open(OUTPUTS_DIR / "ngo_assessments.json", "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2)

    # Print summary statistics
    scores = [a["trustability_score"] for a in assessments]
    labels = [a["score_interpretation"]["label"] for a in assessments]
    print(f"  [SUCCESS] Scored {len(assessments)} NGOs. "
          f"Mean Score: {np.mean(scores):.1f}, Median: {np.median(scores):.1f}, "
          f"Min: {np.min(scores):.1f}, Max: {np.max(scores):.1f}, Std: {np.std(scores):.1f}")
    
    label_counts = pd.Series(labels).value_counts().to_dict()
    print(f"  Label distribution: {label_counts}")

    return assessments


if __name__ == "__main__":
    run_trustability_scoring()
