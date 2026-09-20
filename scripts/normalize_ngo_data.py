"""
ELEOS — Member 1: NGO Data Normalization & Duplicate Detection
Normalizes raw data into standardized formats:
- Cleans and standardizes names (whitespace, casing, punctuation).
- Standardizes dates to ISO YYYY-MM-DD.
- Standardizes monetary values to pure floats (stripping currency symbols, commas).
- Deduplicates multi-value lists (sectors, operational states/districts).
- Identifies and flags potential duplicates based on name similarity and registration numbers.
"""

import os
import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "synthetic"
DATA_DIR = ROOT_DIR / "data" / "reference"


def normalize_text_name(name: str) -> str:
    """Standardizes non-profit name: removes special punctuation, collapses spaces, uppercase."""
    if not isinstance(name, str):
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKD", name)
    # Remove punctuation except alphanumeric and space
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple whitespaces
    tokens = text.strip().split()
    return " ".join(tokens).upper()


def normalize_currency_value(val: Any) -> Optional[float]:
    """Converts any currency string (e.g. '₹ 2,45,000.50') to float."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    # Remove currency symbols (₹, $, Rs, INR) and commas
    cleaned = re.sub(r"[₹$,RsINR\s]", "", val_str)
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_date_iso(date_val: Any) -> Optional[str]:
    """Standardizes dates to YYYY-MM-DD format."""
    if pd.isna(date_val) or date_val is None or str(date_val).strip() == "":
        return None
    try:
        dt = pd.to_datetime(date_val, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def detect_duplicates(df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies potential duplicate NGOs based on normalized name or registration number.
    Flags duplicates without deleting them.
    """
    df = df_master.copy()
    df["is_potential_duplicate"] = False
    df["duplicate_reason"] = None

    # Check for identical normalized names
    name_counts = df["normalized_ngo_name"].value_counts()
    dup_names = set(name_counts[name_counts > 1].index)

    # Check for identical registration numbers
    reg_counts = df["registration_number"].value_counts()
    dup_regs = set(reg_counts[reg_counts > 1].index)

    for idx, row in df.iterrows():
        reasons = []
        if row["normalized_ngo_name"] in dup_names:
            reasons.append("Shared normalized name")
        if row["registration_number"] in dup_regs:
            reasons.append("Shared registration number")
        
        if reasons:
            df.at[idx, "is_potential_duplicate"] = True
            df.at[idx, "duplicate_reason"] = "; ".join(reasons)

    return df


def run_normalization() -> Dict[str, pd.DataFrame]:
    print("[2/7] Running normalization & duplicate detection...")
    
    master_path = DATA_DIR / "ngo_master.csv"
    if not master_path.exists():
        raise FileNotFoundError(f"Missing {master_path}. Run generate_reference_ngos.py first.")

    df_master = pd.read_csv(master_path)
    df_fin = pd.read_csv(DATA_DIR / "financial_reports.csv")

    # 1. Normalize Master
    df_master["normalized_ngo_name"] = df_master["ngo_name"].apply(normalize_text_name)
    df_master["date_of_registration"] = df_master["date_of_registration"].apply(normalize_date_iso)
    df_master = detect_duplicates(df_master)

    # 2. Normalize Financial Reports currency columns
    currency_cols = [
        "total_income", "grant_income", "donation_income", "other_income",
        "fcra_income", "nfcra_income", "total_expenditure", "programme_expenses",
        "administrative_expenses", "fundraising_expenses", "employee_expenses",
        "consultancy_expenses", "material_expenses", "other_expenses",
        "cash_and_bank_balance", "total_assets", "total_liabilities",
        "surplus_or_deficit", "related_party_transactions"
    ]
    for col in currency_cols:
        if col in df_fin.columns:
            df_fin[col] = df_fin[col].apply(normalize_currency_value)

    # Save normalized versions back
    df_master.to_csv(DATA_DIR / "ngo_master.csv", index=False)
    df_fin.to_csv(DATA_DIR / "financial_reports.csv", index=False)

    dup_count = df_master["is_potential_duplicate"].sum()
    print(f"  [SUCCESS] Normalization complete. Flagged potential duplicates: {dup_count}")
    return {"master": df_master, "financial_reports": df_fin}


if __name__ == "__main__":
    run_normalization()

