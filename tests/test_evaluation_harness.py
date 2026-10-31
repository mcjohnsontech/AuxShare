# tests/test_evaluation_harness.py
from evaluation.evaluator import EvaluationHarness

def test_dry_run_evaluation():
    harness = EvaluationHarness()
    metrics = harness.run_dry_run()
    
    assert "summary" in metrics
    s = metrics["summary"]
    assert s["total_tracks"] > 0
    assert 0.0 <= s["match_rate"] <= 1.0
    assert 0.0 <= s["precision"] <= 1.0
    assert 0.0 <= s["recall"] <= 1.0
    
    assert "by_source_platform" in metrics
    assert "spotify" in metrics["by_source_platform"]
    assert "youtube_music" in metrics["by_source_platform"]
    assert "apple_music" in metrics["by_source_platform"]
    
    assert "failure_taxonomy" in metrics
    assert len(metrics["failure_taxonomy"]) > 0

