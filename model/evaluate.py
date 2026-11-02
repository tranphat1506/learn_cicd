"""Model quality gate.

Exit code is the contract with CI:
  0 -> artifact may be released
  1 -> artifact is rejected (metrics regressed or latency too high)

Run `python -m model.evaluate --update-baseline` once to snapshot a baseline.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parent
ARTIFACT_PATH = ROOT / "artifacts" / "model.pkl"
GOLDEN_PATH = ROOT / "data" / "golden.csv"
GATE_PATH = ROOT / "gate.json"
BASELINE_PATH = ROOT / "baseline.json"
REPORT_DIR = ROOT / "reports"
REPORT_PATH = REPORT_DIR / "eval.json"
LATENCY_SAMPLES = 200


def load_golden(features: list[str]) -> tuple[np.ndarray, list[str]]:
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    matrix = np.asarray([[float(row[name]) for name in features] for row in rows], dtype=float)
    labels = [row["target"] for row in rows]
    return matrix, labels


def percentile(values: list[float], pct: float) -> float:
    return float(np.percentile(np.asarray(values), pct))


def evaluate() -> dict[str, float]:
    artifact = joblib.load(ARTIFACT_PATH)
    model = artifact["model"]
    features = artifact["features"]

    matrix, labels = load_golden(features)
    predictions = [artifact["class_names"][int(i)] for i in model.predict(matrix)]

    latencies_ms: list[float] = []
    for row in matrix[:LATENCY_SAMPLES]:
        started = time.perf_counter()
        model.predict(row.reshape(1, -1))
        latencies_ms.append((time.perf_counter() - started) * 1000)

    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro")),
        "p95_latency_ms": round(percentile(latencies_ms, 95), 2),
        "golden_rows": float(len(labels)),
        "model_version": artifact.get("version", "unknown"),
    }


def check_gate(metrics: dict[str, float], baseline: dict[str, float], gate: dict) -> list[str]:
    failures: list[str] = []
    if metrics["accuracy"] < gate["min_accuracy"]:
        failures.append(
            f"accuracy {metrics['accuracy']:.4f} < min_accuracy {gate['min_accuracy']:.4f}"
        )

    drop = baseline["accuracy"] - metrics["accuracy"]
    if drop > gate["max_accuracy_drop"]:
        failures.append(
            f"accuracy dropped {drop:.4f} > allowed {gate['max_accuracy_drop']:.4f} "
            f"(baseline {baseline['accuracy']:.4f})"
        )

    if metrics["macro_f1"] < gate["min_macro_f1"]:
        failures.append(
            f"macro_f1 {metrics['macro_f1']:.4f} < min_macro_f1 {gate['min_macro_f1']:.4f}"
        )

    if metrics["p95_latency_ms"] > gate["max_p95_latency_ms"]:
        failures.append(
            f"p95 latency {metrics['p95_latency_ms']:.2f}ms > "
            f"{gate['max_p95_latency_ms']}ms"
        )
    return failures


def print_report(
    metrics: dict[str, float], baseline: dict[str, float], failures: list[str]
) -> None:
    print("\n| metric | baseline | current |")
    print("|---|---|---|")
    for key in ("accuracy", "macro_f1", "p95_latency_ms"):
        print(f"| {key} | {baseline.get(key, 'n/a')} | {metrics[key]} |")

    if failures:
        print("\nREJECTED:")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("\nACCEPTED: all gates passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="snapshot current metrics as the new baseline (review this in a PR!)",
    )
    args = parser.parse_args()

    if not ARTIFACT_PATH.exists():
        print(f"artifact missing: {ARTIFACT_PATH}. Run `make seed` first.", file=sys.stderr)
        return 1
    if not GOLDEN_PATH.exists():
        print(f"golden set missing: {GOLDEN_PATH}. Run `make seed` first.", file=sys.stderr)
        return 1

    metrics = evaluate()
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))

    if args.update_baseline or not BASELINE_PATH.exists():
        BASELINE_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print(f"baseline written: {BASELINE_PATH}")
        baseline = metrics
        failures: list[str] = []
    else:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        failures = check_gate(metrics, baseline, gate)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps({"metrics": metrics, "baseline": baseline, "failures": failures}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    print_report(metrics, baseline, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
