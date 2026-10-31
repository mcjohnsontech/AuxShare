# backend/evaluation/evaluator.py
import json
import os
import sys
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add backend directory to sys.path so imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from evaluation.vcr_client import VCRReplayContext
from platform_detector import PlatformDetector

class EvaluationHarness:
    def __init__(self, dataset_path: Optional[str] = None):
        if not dataset_path:
            dataset_path = os.path.join(current_dir, "fixtures", "evaluation_dataset.json")
        self.dataset_path = dataset_path
        self.detector = PlatformDetector()

    def load_dataset(self) -> List[Dict[str, Any]]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_dry_run(self) -> Dict[str, Any]:
        """
        Run the evaluation dataset in dry-run mode under VCR replay.
        Never writes any playlists to external platforms.
        """
        dataset = self.load_dataset()
        results: List[Dict[str, Any]] = []

        with VCRReplayContext():
            for item in dataset:
                source_track = item["source_track"]
                target_platform_name = item["target_platform"]
                target_platform = self.detector.get_platform(target_platform_name)

                if not target_platform:
                    raise ValueError(f"Unknown target platform: {target_platform_name}")

                # Call matcher in dry run
                match_result = target_platform.match_track(source_track)

                matched_id = match_result.get("id") if match_result else None
                confidence = match_result.get("confidence", 0.0) if match_result else 0.0
                match_method = match_result.get("match_method") if match_result else None

                expected_target_id = item.get("expected_target_id")
                expected_is_match = item.get("expected_is_match", True)
                failure_cat = item.get("failure_category")

                # Classification
                # True Positive: match found, expected to match, and matched the right track
                if matched_id and expected_is_match and matched_id == expected_target_id:
                    outcome = "TP"
                # False Positive: match found, but it shouldn't match OR matched wrong track
                elif matched_id and (not expected_is_match or matched_id != expected_target_id):
                    outcome = "FP"
                # False Negative: no match found, but it was expected to match
                elif not matched_id and expected_is_match:
                    outcome = "FN"
                # True Negative: correctly avoided matching a negative/unmatched track
                else:
                    outcome = "TN"

                results.append({
                    "id": item["id"],
                    "source_platform": item["source_platform"],
                    "target_platform": target_platform_name,
                    "title": source_track.get("title"),
                    "artist": source_track.get("artist"),
                    "matched_id": matched_id,
                    "expected_target_id": expected_target_id,
                    "expected_is_match": expected_is_match,
                    "confidence": confidence,
                    "match_method": match_method,
                    "outcome": outcome,
                    "failure_category": failure_cat
                })

        return self.compute_metrics(results)

    def compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        tp = sum(1 for r in results if r["outcome"] == "TP")
        fp = sum(1 for r in results if r["outcome"] == "FP")
        fn = sum(1 for r in results if r["outcome"] == "FN")
        tn = sum(1 for r in results if r["outcome"] == "TN")

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        match_rate = (tp + fp) / total if total > 0 else 0.0

        # Breakdown by source platform
        by_source = defaultdict(lambda: {"total": 0, "tp": 0, "fp": 0, "fn": 0, "tn": 0})
        for r in results:
            src = r["source_platform"]
            by_source[src]["total"] += 1
            by_source[src][r["outcome"].lower()] += 1

        source_metrics = {}
        for src, counts in by_source.items():
            s_total = counts["total"]
            s_tp = counts["tp"]
            s_fp = counts["fp"]
            s_fn = counts["fn"]
            s_prec = s_tp / (s_tp + s_fp) if (s_tp + s_fp) > 0 else 0.0
            s_rate = (s_tp + s_fp) / s_total if s_total > 0 else 0.0
            source_metrics[src] = {
                "total": s_total,
                "tp": s_tp,
                "fp": s_fp,
                "fn": s_fn,
                "tn": counts["tn"],
                "match_rate": s_rate,
                "precision": s_prec
            }

        # Failure taxonomy counts (for all errors: FP and FN)
        failure_taxonomy = defaultdict(int)
        for r in results:
            if r["outcome"] in ("FP", "FN"):
                cat = r["failure_category"] or "unclassified"
                failure_taxonomy[cat] += 1

        return {
            "summary": {
                "total_tracks": total,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
                "match_rate": match_rate,
                "precision": precision,
                "recall": recall
            },
            "by_source_platform": source_metrics,
            "failure_taxonomy": dict(failure_taxonomy),
            "results": results
        }

    def format_report(self, metrics: Dict[str, Any]) -> str:
        s = metrics["summary"]
        report = []
        report.append("# Baseline Evaluation Report (Phase 0)")
        report.append(f"**Total Evaluated Tracks**: {s['total_tracks']}")
        report.append(f"**Overall Match Rate**: {s['match_rate']:.1%}")
        report.append(f"**Precision**: {s['precision']:.1%}  *(Target: Priority #1 - avoid wrong songs)*")
        report.append(f"**Recall**: {s['recall']:.1%}")
        report.append(f"**Outcomes**: TP={s['true_positives']}, FP={s['false_positives']}, FN={s['false_negatives']}, TN={s['true_negatives']}\n")

        report.append("## Metrics per Source Platform")
        report.append("| Source Platform | Total | Matched | Match Rate | Precision | TP | FP | FN |")
        report.append("|---|---|---|---|---|---|---|---|")
        for src, data in metrics["by_source_platform"].items():
            matched = data["tp"] + data["fp"]
            report.append(f"| {src} | {data['total']} | {matched} | {data['match_rate']:.1%} | {data['precision']:.1%} | {data['tp']} | {data['fp']} | {data['fn']} |")
        report.append("")

        report.append("## Failure Taxonomy Counts")
        report.append("| Failure Category | Error Count | Description / Root Cause |")
        report.append("|---|---|---|")
        descriptions = {
            "remaster": "Remaster suffix differences in title comparison",
            "different_isrc": "ISRC differs across album/compilation editions",
            "regional": "Track unavailable or geo-restricted in target market",
            "live_vs_studio": "Live version matched instead of studio recording (FP)",
            "remix_penalty": "Remix or sped-up/acoustic matched original song (FP)",
            "featured_artist_formatting": "Delimiter differences ('feat.', 'with', '&') causing mismatch",
            "non_latin_script": "Non-Latin characters (Kanji, Hangul, Cyrillic, Arabic) vs Romanized title",
            "youtube_noise": "YouTube video artifacts ('Official Video', 'Lyrics', '- Topic') in title",
            "genuinely_missing": "Track does not exist in target catalog"
        }
        for cat, count in sorted(metrics["failure_taxonomy"].items(), key=lambda x: x[1], reverse=True):
            desc = descriptions.get(cat, "Other edge case")
            report.append(f"| `{cat}` | {count} | {desc} |")

        return "\n".join(report)

if __name__ == "__main__":
    harness = EvaluationHarness()
    metrics = harness.run_dry_run()
    print(harness.format_report(metrics))

