"""Reference calculations for candidate acceptance protocols, never model acceptance."""
import argparse
import json
import math

from generate_interface_docs import ROOT, digest


def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def classification(data):
    labels = data["labels"]
    assert labels and len(labels) == len(set(labels))
    counts = {label: {"tp": 0, "fp": 0, "fn": 0} for label in labels}
    failures, unknown = 0, 0
    for sample in data["samples"]:
        assert set(sample["predicted"]) <= set(labels)
        failures += sample["status"] != "SUCCEEDED"
        if sample["truth"] is None:
            unknown += 1
            continue
        truth = set(sample["truth"])
        predicted = set(sample["predicted"]) if sample["status"] == "SUCCEEDED" else set()
        assert truth <= set(labels) and set(sample["predicted"]) <= set(labels)
        for label in labels:
            counts[label]["tp"] += label in truth and label in predicted
            counts[label]["fp"] += label not in truth and label in predicted
            counts[label]["fn"] += label in truth and label not in predicted
    result = {}
    for label, c in counts.items():
        f1_denominator = 2 * c["tp"] + c["fp"] + c["fn"]
        result[label] = dict(c, recall=safe_ratio(c["tp"], c["tp"] + c["fn"]),
                             f1=(2 * c["tp"] / f1_denominator if f1_denominator else 0),
                             positive_support=c["tp"] + c["fn"])
    return {"per_label": result, "macro_f1": sum(v["f1"] for v in result.values()) / len(labels),
            "zero_division_f1_policy": 0, "samples": len(data["samples"]), "failed_samples": failures,
            "unknown_truth_samples": unknown, "eligible_truth_samples": len(data["samples"]) - unknown,
            "zero_positive_labels": [label for label, c in counts.items() if c["tp"] + c["fn"] == 0]}


def mask_iou(data):
    values, negatives, negative_false_alarms = [], 0, 0
    for sample in data["samples"]:
        truth, predicted = sample["truth"], sample["predicted"]
        assert len(truth) == len(predicted) and truth
        assert set(truth + predicted) <= {0, 1}
        predicted = predicted if sample["status"] == "SUCCEEDED" else [0] * len(truth)
        if not any(truth):
            negatives += 1
            negative_false_alarms += any(predicted)
            continue
        intersection = sum(a and b for a, b in zip(truth, predicted))
        union = sum(a or b for a, b in zip(truth, predicted))
        values.append(intersection / union)
    return {"positive_image_macro_iou": safe_ratio(sum(values), len(values)), "positive_images": len(values),
            "negative_images": negatives, "negative_image_false_alarm_rate": safe_ratio(negative_false_alarms, negatives),
            "positive_image_values": values}


def retrieval(data):
    assert isinstance(data["k"], int) and data["k"] > 0
    hits, item_recalls, unknown, failed = 0, [], 0, 0
    for sample in data["samples"]:
        truth = set(sample["relevant_ids"])
        assert len(sample["ranked_ids"]) == len(set(sample["ranked_ids"]))
        if not truth:
            unknown += 1
            continue
        ranked = sample["ranked_ids"][:data["k"]] if sample["status"] == "SUCCEEDED" else []
        found = len(truth & set(ranked))
        hits += found > 0
        failed += sample["status"] != "SUCCEEDED"
        item_recalls.append(found / len(truth))
    return {"query_hit_rate_at_k": safe_ratio(hits, len(item_recalls)),
            "query_macro_item_recall_at_k": safe_ratio(sum(item_recalls), len(item_recalls)),
            "eligible_queries": len(item_recalls), "unknown_or_no_relevant_queries": unknown,
            "failed_eligible_queries": failed, "hits": hits, "k": data["k"]}


def boundaries(data):
    errors, unmatched = [], 0
    for sample in data["samples"]:
        truth = sample["truth_range_ms"]
        assert len(truth) == 2 and 0 <= truth[0] < truth[1]
        predicted = sample["predicted_range_ms"]
        if sample["status"] != "SUCCEEDED" or predicted is None:
            unmatched += 1
            continue
        assert len(predicted) == 2 and 0 <= predicted[0] < predicted[1]
        errors.append((abs(truth[0] - predicted[0]) + abs(truth[1] - predicted[1])) / 2 / 1000)
    return {"matched_mean_boundary_error_seconds": safe_ratio(sum(errors), len(errors)),
            "matched_segments": len(errors), "unmatched_segments": unmatched,
            "matched_coverage": safe_ratio(len(errors), len(data["samples"]))}


def origin_top3(data):
    hits, known, unknown, false_certainty = 0, 0, 0, 0
    for sample in data["samples"]:
        candidates = sample["candidate_ids"]
        assert len(candidates) <= 3 and len(candidates) == len(set(candidates))
        if sample["reference_asset_id"] is None:
            unknown += 1
            false_certainty += sample["claims_certain_origin"]
            continue
        known += 1
        hits += sample["status"] == "SUCCEEDED" and sample["reference_asset_id"] in candidates
    return {"known_reference_top3_hit_rate": safe_ratio(hits, known), "known_reference_clusters": known,
            "unknown_reference_clusters": unknown, "unknown_false_certainty": false_certainty}


def latency(data):
    assert math.isfinite(data["measurement_seconds"]) and data["measurement_seconds"] > 0
    accepted = [r for r in data["requests"] if r["accepted"]]
    success = [r for r in accepted if r["terminal_status"] == "SUCCEEDED"]
    for row in data["requests"]:
        assert row["latency_ms"] is None or math.isfinite(row["latency_ms"]) and row["latency_ms"] >= 0
    terminal = {"SUCCEEDED", "FAILED", "CANCELLED", "TIMEOUT", "TIMED_OUT"}
    observed = sorted(r["latency_ms"] for r in accepted if r["latency_ms"] is not None and r["terminal_status"] in terminal)
    percentiles = {f"p{p}_ms": observed[max(0, math.ceil(p / 100 * len(observed)) - 1)] if observed else None for p in [50, 95, 99]}
    return dict(percentiles, accepted_tasks=len(accepted), successful_tasks=len(success),
                accepted_success_rate=safe_ratio(len(success), len(accepted)),
                observed_terminal_latencies=len(observed),
                missing_latency_observations=len(accepted) - len(observed),
                accepted_nonterminal_tasks=sum(r["terminal_status"] not in terminal for r in accepted),
                rejected_requests=len(data["requests"]) - len(accepted),
                quantile_method="nearest_rank", successful_throughput_per_second=safe_ratio(len(success), data["measurement_seconds"]))


def ece(data):
    assert isinstance(data["bins"], int) and data["bins"] > 0
    bins = [{"count": 0, "confidence_sum": 0, "correct_sum": 0} for _ in range(data["bins"])]
    invalid = 0
    for row in data["predictions"]:
        confidence = row["confidence"]
        if confidence is None:
            invalid += 1
            continue
        assert 0 <= confidence <= 1
        slot = min(data["bins"] - 1, int(confidence * data["bins"]))
        bins[slot]["count"] += 1
        bins[slot]["confidence_sum"] += confidence
        bins[slot]["correct_sum"] += bool(row["correct"])
    total = sum(b["count"] for b in bins)
    value = sum(abs(b["correct_sum"] - b["confidence_sum"]) for b in bins) / total if total else None
    return {"ece": value, "valid_confidence_predictions": total, "invalid_confidence_predictions": invalid,
            "binning": "equal_width_left_closed_right_open_last_includes_one", "bins": bins}


def citations(data):
    rows = data["conclusions"]
    complete = sum(all(r[k] for k in ["reference_exists", "object_version_fixed", "digest_matches", "currently_authorized", "supports_statement"]) for r in rows)
    return {"fully_traceable_conclusions": complete, "conclusions": len(rows),
            "full_traceability_rate": safe_ratio(complete, len(rows)),
            "semantic_support_rate": safe_ratio(sum(r["supports_statement"] for r in rows), len(rows))}


EVALUATORS = {"classification": classification, "mask_iou": mask_iou, "retrieval": retrieval,
              "boundaries": boundaries, "origin_top3": origin_top3, "latency": latency, "ece": ece, "citations": citations}


def self_test():
    fixture_path = "tests/fixtures/acceptance-metric-reference.json"
    fixtures = json.loads((ROOT / fixture_path).read_text(encoding="utf-8"))
    checks = []
    for fixture in fixtures["cases"]:
        result = EVALUATORS[fixture["evaluator"]](fixture["input"])
        for key, expected in fixture["expected"].items():
            actual = result[key]
            assert actual == expected or isinstance(actual, (float, int)) and isinstance(expected, (float, int)) and math.isclose(actual, expected, abs_tol=1e-12), (fixture["name"], key, actual, expected)
        checks.append({"name": fixture["name"], "status": "PASS", "computed": result})
    report = {"status": "PASS", "scope": "reference_formula_and_failure_counting_on_synthetic_fixtures_not_real_model_acceptance",
              "checks": checks, "formal_business_acceptance": False,
              "source_hashes": {p: digest(p) for p in [fixture_path, "scripts/evaluate_acceptance_metrics.py"]}}
    output = ROOT / "docs/00-project/validation/acceptance-metric-reference-report.json"
    output.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": "PASS", "checks": len(checks), "formal_business_acceptance": False}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--evaluator", choices=EVALUATORS)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        assert args.input and args.evaluator, "specify --self-test or --input and --evaluator"
        with open(args.input, encoding="utf-8") as stream:
            result = EVALUATORS[args.evaluator](json.load(stream))
        print(json.dumps({"metrics": result, "formal_acceptance_verdict": "NOT_ISSUED"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
