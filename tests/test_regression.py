# tests/test_regression.py
import json
import os
from evaluation.evaluator import EvaluationHarness

def test_precision_regression_check():
    """Precision must never drop below the frozen Phase 0 baseline."""
    baseline_path = os.path.join(os.path.dirname(__file__), "..", "backend", "evaluation", "baseline.json")
    assert os.path.exists(baseline_path), "baseline.json must exist"
    
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline = json.load(f)
        
    baseline_precision = baseline["summary"]["precision"]
    
    harness = EvaluationHarness()
    current_metrics = harness.run_dry_run()
    current_precision = current_metrics["summary"]["precision"]
    
    # Regression guard: precision must not drop
    assert current_precision >= baseline_precision, (
        f"Regression detected! Precision dropped from {baseline_precision:.1%} to {current_precision:.1%}"
    )

