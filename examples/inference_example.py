#!/usr/bin/env python3
"""Example usage of the Kev-WCAG model for accessibility evaluation.

This script demonstrates how to load a trained Kev-WCAG checkpoint and
run accessibility evaluations on HTML patterns using the Kev typed-question API.
"""

import json
from pathlib import Path


def load_kev_model(model_path: str, device: str = "cpu"):
    """Load a trained Kev checkpoint.

    Uses Kev's Checkpoint API to load base model + LoRA adapter + head.
    Returns (model, tokenizer) where model supports .eval() with typed questions.
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


def evaluate_html(model, tok, html: str, description: str) -> dict:
    """Evaluate a single HTML pattern for WCAG accessibility.

    Uses Kev's typed-question interface with noul/choice/score questions.
    """
    state = (
        f"Analyze this HTML for WCAG 2.2 accessibility issues.\n\n"
        f"HTML pattern: {description}\n\n"
        f"HTML:\n{html}\n\n"
        f"Please answer the following questions about accessibility compliance."
    )

    # Run the model evaluation with typed questions
    prediction = model.eval({
        "state": state,
        "questions": {
            "has_violation": {
                "type": "noul",
                "instructions": "Does this HTML have a WCAG 2.2 accessibility violation?",
                "criteria": {"true": "Yes, violation present", "false": "No violation"},
            },
            "which_criterion": {
                "type": "choice",
                "instructions": "Which WCAG 2.2 success criterion is violated?",
                "criteria": {
                    "1.1.1 Non-text Content": "Missing text alternatives for non-text content",
                    "1.3.1 Info and Relationships": "Missing semantic structure or relationships",
                    "1.4.3 Contrast": "Insufficient color contrast",
                    "2.4.4 Link Purpose": "Link purpose not clear from link text",
                    "2.4.7 Focus Visible": "Keyboard focus indicator not visible",
                    "4.1.2 Name Role Value": "Missing accessible name, role, or value",
                    "No WCAG 2.2 violation": "This pattern is fully accessible",
                },
            },
            "severity": {
                "type": "score",
                "instructions": "Rate the accessibility severity (0-4 scale).",
                "criteria": [
                    "0: No accessibility issue (fully accessible)",
                    "1: Minor issue (low impact, easy workaround)",
                    "2: Moderate issue (affects some users, medium impact)",
                    "3: Significant issue (affects many users, high impact)",
                    "4: Critical issue (blocks access entirely, severe impact)",
                ],
            },
        },
    })

    return {
        "description": description,
        "html": html,
        "has_violation": prediction.get("has_violation"),
        "which_criterion": prediction.get("which_criterion"),
        "severity": prediction.get("severity"),
        "raw_prediction": prediction,
    }


def main():
    """Run demo evaluations on sample HTML patterns."""
    print("=" * 70)
    print("  Kev-WCAG Accessibility Evaluation Demo")
    print("=" * 70)

    # Load the trained model
    model_path = "/kaggle/working/kev-wcag-model"
    print(f"Loading model from: {model_path}")
    try:
        model, tok = load_kev_model(model_path, device="cpu")
        print(f"✓ Model loaded successfully: {type(model).__name__}")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print("\nTo use this demo:")
        print("1. First run the Kaggle training notebook:")
        print("   https://www.kaggle.com/code/hummern/wcag-kev-train")
        print("2. The notebook saves the trained model to /kaggle/working/kev-wcag-model/")
        print("3. Then run this script again")
        return

    # Demo patterns covering different WCAG criteria
    demo_patterns = [
        {
            "html": '<img src="photo.jpg">',
            "description": "Image without alt attribute",
        },
        {
            "html": '<img src="ornament.svg" alt="">',
            "description": "Decorative image with empty alt text (correct)",
        },
        {
            "html": '<p style="color:#999; background:white;">Medium gray text on white</p>',
            "description": "Low contrast text (WCAG 1.4.3 violation)",
        },
        {
            "html": '<form><input type="text" placeholder="Name"></form>',
            "description": "Form input without label (WCAG 3.3.2 violation)",
        },
        {
            "html": '<a href="/page"><img src="product.jpg" alt="product"></a>',
            "description": "Linked image without descriptive alt text",
        },
        {
            "html": '<label for="email">Email address</label><input type="email" id="email">',
            "description": "Properly labeled input (WCAG compliant)",
        },
        {
            "html": '<button onclick="submit()">Submit</button>',
            "description": "Button with accessible name from content",
        },
        {
            "html": '<div role="button" aria-label="Close" onclick="close()">✕</div>',
            "description": "Custom button with ARIA label (WCAG compliant)",
        },
    ]

    print(f"\nEvaluating {len(demo_patterns)} HTML patterns:\n")
    print("-" * 70)

    results = []
    for pattern in demo_patterns:
        result = evaluate_html(model, tok, pattern["html"], pattern["description"])
        results.append(result)

        # Print result for this pattern
        violation = "YES" if result["has_violation"] else "no"
        criterion = result["which_criterion"] or "none"
        severity = result["severity"] if result["severity"] is not None else "?"
        print(f"Pattern: {result['description']}")
        print(f"  HTML: {result['html']}")
        print(f"  Violation: {violation}")
        print(f"  Criterion: {criterion}")
        print(f"  Severity: {severity}/4")
        print()

    # Summary statistics
    correct_violation = sum(
        1
        for r in results
        if (r["has_violation"] == True and "alt" not in r["html"].lower())
        or (r["has_violation"] == False and "alt" in r["html"].lower() and ('alt=""' in r["html"] or 'aria-label' in r["html"] or 'label' in r["html"].lower()))
    )
    total = len(results)
    print("-" * 70)
    print(f"  Demo completed: {total} patterns evaluated")
    print("  Note: This is a demo - for full evaluation see evaluation/evaluate.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
