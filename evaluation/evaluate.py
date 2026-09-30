"""Evaluate Kev-WCAG model on accessibility patterns.

Uses current Kev format: questions as dict with type/instructions/criteria/label.
"""

import json
import argparse
from pathlib import Path


def load_dataset(path: str) -> list[dict]:
    """Load WCAG training dataset from JSONL file (current Kev format)."""
    with open(path) as f:
        return [json.loads(line) for line in f]


def evaluate_model(model, dataset: list[dict]) -> dict:
    """Evaluate model on dataset and return metrics."""
    results = {
        "total": len(dataset),
        "violation_detection": {"correct": 0, "total": 0},
        "criterion_identification": {"correct": 0, "total": 0},
        "severity_estimation": {"correct": 0, "total": 0, "within_tolerance": 0},
    }

    for record in dataset:
        questions = record["questions"]

        # Run model prediction with label=None (model fills in)
        prediction = model.eval({
            "state": record["state"],
            "questions": {
                k: {**v, "label": None} if v["label"] is not None else v
                for k, v in questions.items()
            },
        })

        # Evaluate violation detection (has_violation)
        if "has_violation" in questions:
            results["violation_detection"]["total"] += 1
            expected = questions["has_violation"]["label"]
            pred = prediction.get("has_violation")
            if pred == expected:
                results["violation_detection"]["correct"] += 1

        # Evaluate criterion identification (which_criterion)
        if "which_criterion" in questions:
            results["criterion_identification"]["total"] += 1
            expected = questions["which_criterion"]["label"]
            pred = prediction.get("which_criterion")
            if pred == expected:
                results["criterion_identification"]["correct"] += 1

        # Evaluate severity estimation (severity)
        if "severity" in questions:
            results["severity_estimation"]["total"] += 1
            expected = questions["severity"]["label"]
            pred = prediction.get("severity")
            if pred is not None and abs(int(pred) - int(expected)) <= 1:
                results["severity_estimation"]["within_tolerance"] += 1
            if pred == expected:
                results["severity_estimation"]["correct"] += 1

    # Calculate accuracies
    for key in ["violation_detection", "criterion_identification", "severity_estimation"]:
        total = results[key]["total"]
        if total > 0:
            results[key]["accuracy"] = results[key]["correct"] / total
            if "within_tolerance" in results[key]:
                results[key]["accuracy_tolerance"] = results[key]["within_tolerance"] / total

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate Kev-WCAG model")
    parser.add_argument("--model", type=str, required=True, help="Path to model or model name")
    parser.add_argument("--data", type=str, default="data/wcag/wcag_train_kev.jsonl", help="Dataset path (current Kev format)")
    parser.add_argument("--output", type=str, default="evaluation/eval_results.json", help="Results output path")
    args = parser.parse_args()

    print(f"Loading model: {args.model}")
    print(f"Loading dataset: {args.data}")

    dataset = load_dataset(args.data)
    print(f"Loaded {len(dataset)} examples")

    # This is a placeholder - actual evaluation requires the trained model
    print("Evaluation code ready - needs trained model to run")
    print("Run training first: see training/kaggle_notebook.ipynb")


if __name__ == "__main__":
    main()
