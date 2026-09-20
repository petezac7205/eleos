"""
ELEOS — Member 1: Master Pipeline Orchestrator
Executes the full end-to-end data processing, modelling, and assessment generation:
1. Reference dataset generation (200 NGOs)
2. Normalization & deduplication
3. Feature engineering & peer grouping
4. Isolation Forest unsupervised anomaly detection
5. Evidence-based trustability scoring
6. Accounting consistency validation
7. Bias & fairness diagnostics
8. Sensitivity & rank stability analysis
"""

import sys
import time
import argparse
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_reference_ngos import generate_reference_data
from scripts.normalize_ngo_data import run_normalization
from scripts.feature_engineering import run_feature_engineering
from scripts.financial_anomaly_detection import run_anomaly_detection, DEFAULT_CONTAMINATION
from scripts.trustability_scoring import run_trustability_scoring
from scripts.validate_reference_data import run_reference_validation
from scripts.bias_analysis import compute_correlations_and_group_metrics
from scripts.sensitivity_analysis import run_sensitivity_analysis


def run_pipeline(num_ngos: int = 200, contamination: float = DEFAULT_CONTAMINATION):
    start_time = time.time()
    print("=" * 70)
    print("  ELEOS MEMBER 1: DATA, MODELLING & SCORING PIPELINE")
    print("=" * 70)
    print(f"Target NGO Count   : {num_ngos}")
    print(f"Contamination Rate : {contamination}")
    print("-" * 70)

    # 1. Generation
    generate_reference_data(num_ngos=num_ngos)

    # 2. Normalization
    run_normalization()

    # 3. Feature Engineering
    run_feature_engineering()

    # 4. Anomaly Detection
    run_anomaly_detection(contamination=contamination)

    # 5. Scoring & JSON generation
    assessments = run_trustability_scoring()

    # 6. Accounting Validation
    val_report = run_reference_validation()

    # 7. Bias & Fairness Diagnostics
    bias_report = compute_correlations_and_group_metrics()

    # 8. Sensitivity Analysis
    sens_report = run_sensitivity_analysis()

    elapsed = round(time.time() - start_time, 2)
    print("=" * 70)
    print(f"  PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s")
    print("=" * 70)
    print(f"Total NGO Assessments Output : {len(assessments)}")
    print(f"Accounting Reconciliation    : {val_report['accounting_reconciliation_audit']['expense_breakdown_reconciliation_rate']}%")
    print(f"Sensitivity Verdict          : {sens_report['stability_verdict']}")
    print(f"Output Directory             : {REPO_ROOT / 'outputs'}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete Member 1 pipeline")
    parser.add_argument("--count", type=int, default=200, help="Number of reference NGOs to generate")
    parser.add_argument("--contamination", type=float, default=DEFAULT_CONTAMINATION, help="Isolation forest contamination")
    args = parser.parse_args()

    run_pipeline(num_ngos=args.count, contamination=args.contamination)

