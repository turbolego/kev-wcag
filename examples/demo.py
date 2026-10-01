"""Demo: run the trained Kev-WCAG model for accessibility evaluation.

Usage:
    python examples/demo.py                     # uses local model if available
    python examples/demo.py --model /path/to/kev-wcag
    python examples/demo.py --help

The demo evaluates 5 WCAG HTML patterns and prints predictions.
Requires the trained Kev checkpoint (adapter_model.safetensors + head.pt).
"""

import argparse
import json
from pathlib import Path


def load_checkpoint(model_path: str, device: str = "cpu"):
    """Load a trained Kev checkpoint.

    Uses Kev's Checkpoint API which handles base model + LoRA adapter + head.
    """
    from kev.checkpoint import Checkpoint

    ckpt = Checkpoint(model_path)
    loaded = ckpt.load(device=device)
    # Checkpoint.load returns (tokenizer, model)
    if len(loaded) == 2:
        tok, model = loaded
    else:
        model = loaded[0]
        tok = loaded[1]
    return model, tok


def run_evaluation(model, tok, patterns: list[dict]) -> list[dict]:
    """Run Kev-WCAG on a list of HTML patterns.

    Each pattern: {"desc": str, "html": str, "expected_violation": bool}
    Returns: list of {pattern, predictions, expected}
    """
    results = []
    for pat in patterns:
        state = (
            f"Analyze this HTML for WCAG 2.2 accessibility issues.\n\n"
            f"HTML pattern: {pat['desc']}\n\n"
            f"HTML:\n{pat['html']}\n\n"
            f"For each question, provide your answer."
        )

        prediction = model.eval({
            "state": state,
            "questions": {
                "has_violation": {
                    "type": "noul",
                    "instructions": "Does this HTML have a WCAG accessibility violation?",
                },
                "which_criterion": {
                    "type": "choice",
                    "instructions": "Which WCAG 2.2 success criterion applies?",
                    "criteria": {
                        "1.1.1 Non-text Content": None,
                        "1.3.1 Info and Relationships": None,
                        "1.4.3 Contrast": None,
                        "2.4.4 Link Purpose": None,
                        "2.4.7 Focus Visible": None,
                        "4.1.2 Name Role Value": None,
                        "No WCAG 2.2 violation": None,
                    },
                },
                "severity": {
                    "type": "score",
                    "instructions": "Rate the accessibility severity.",
                    "criteria": [
                        "0: No accessibility issue",
                        "1: Minor issue",
                        "2: Moderate issue",
                        "3: Significant issue",
                        "4: Critical issue — blocks access",
                    ],
                },
            },
        })

        results.append({
            "pattern": pat["desc"],
            "html": pat["html"],
            "expected_violation": pat["expected_violation"],
            "has_violation": prediction.get("has_violation"),
            "which_criterion": prediction.get("which_criterion"),
            "severity": prediction.get("severity"),
        })
    return results


def print_results(results: list[dict]):
    """Pretty-print evaluation results."""
    print("\n" + "=" * 60)
    print("  Kev-WCAG Accessibility Evaluation Demo")
    print("=" * 60)

    for r in results:
        expected = "YES" if r["expected_violation"] else "no"
        predicted = "YES" if r["has_violation"] else "no"
        match = "✓" if (r["has_violation"] == r["expected_violation"]) else "✗"

        print(f"\n{match} Pattern: {r['pattern']}")
        print(f"   HTML: {r['html'][:80]}")
        print(f"   Expected violation: {expected}")
        print(f"   Predicted violation: {predicted}")
        if r["which_criterion"]:
            print(f"   Predicted criterion: {r['which_criterion']}")
        if r["severity"] is not None:
            print(f"   Predicted severity: {r['severity']}")

    # Summary
    correct = sum(
        1
        for r in results
        if r["has_violation"] == r["expected_violation"]
    )
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"  Results: {correct}/{total} correct")
    print(f"{'=' * 60}\n")


# ── Demo patterns: diverse WCAG examples ──
DEMO_PATTERNS = [
    {
        "desc": "Image without alt attribute",
        "html": '<img src="photo.jpg">',
        "expected_violation": True,
    },
    {
        "desc": "Decorative image with empty alt (correct)",
        "html": '<img src="ornament.svg" alt="">',
        "expected_violation": False,
    },
    {
        "desc": "Low contrast text",
        "html": '<p style="color:#999; background:white;">Medium gray text on white</p>',
        "expected_violation": True,
    },
    {
        "desc": "Missing form label",
        "html": '<form><input type="text" placeholder="Name"></form>',
        "expected_violation": True,
    },
    {
        "desc": "Linked image without alt",
        "html": '<a href="/page"><img src="product.jpg" alt="product"></a>',
        "expected_violation": True,
    },
    {
        "desc": "Properly labeled input (correct)",
        "html": '<label for="email">Email address</label><input type="email" id="email">',
        "expected_violation": False,
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Run Kev-WCAG accessibility evaluation demo"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="/kaggle/working/kev-wcag-model",
        help="Path to trained Kev checkpoint (default: /kaggle/working/kev-wcag-model)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device: cpu or cuda (default: cpu)",
    )
    parser.add_argument(
        "--patterns",
        type=str,
        default=None,
        help="JSON file with custom patterns (default: built-in demo patterns)",
    )
    args = parser.parse_args()

    # Load model
    model_path = args.model
    if not Path(model_path).exists():
        print(f"Model not found at {model_path}")
        print("\nOptions:")
        print("  1. Run the Kaggle training notebook first:")
        print("     https://www.kaggle.com/code/hummern/wcag-kev-train")
        print("  2. Or train locally with: python training/convert_data.py")
        print("     and the Kev training pipeline")
        print()
        return

    print(f"Loading Kev-WCAG model from: {model_path}")
    model, tok = load_checkpoint(model_path, device=args.device)
    print(f"Model loaded: {type(model).__name__}")

    # Load patterns
    if args.patterns:
        with open(args.patterns) as f:
            patterns = json.load(f)
    else:
        patterns = DEMO_PATTERNS

    # Run evaluation
    results = run_evaluation(model, tok, patterns)
    print_results(results)


if __name__ == "__main__":
    main()
