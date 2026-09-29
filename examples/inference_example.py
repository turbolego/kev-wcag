#!/usr/bin/env python3
"""Example usage of the Kev-WCAG model for accessibility evaluation."""

import json
from pathlib import Path


def load_model(model_path: str):
    """Load the Kev-WCAG model."""
    from kev.model import AutoModelForCausalLM
    
    # Try to load local model first, then fallback to remote
    if Path(model_path).exists():
        model = AutoModelForCausalLM.from_pretrained(model_path)
    else:
        # Use HuggingFace model if available
        model = AutoModelForCausalLM.from_pretrained(model_path)
    
    return model


def evaluate_pattern(model, html: str, pattern_desc: str) -> dict:
    """Evaluate a single HTML pattern for accessibility issues."""
    
    state = f"""Identify accessibility issues in this HTML pattern.

Pattern: {pattern_desc}

HTML:
{html}
"""
    
    result = model.eval({
        "state": state,
        "questions": [
            {
                "type": "noul",
                "instr": f"Does this HTML pattern have a WCAG accessibility violation? Pattern: {pattern_desc}",
            },
            {
                "type": "choice",
                "instr": f"Which WCAG 2.2 success criterion does this pattern violate? Pattern: {pattern_desc}",
                "options": [
                    "1.1.1 Non-text Content",
                    "1.2.2 Captions",
                    "1.3.1 Info and Relationships",
                    "1.4.3 Contrast",
                    "2.1.1 Keyboard",
                    "2.4.4 Link Purpose",
                    "2.4.7 Focus Visible",
                    "4.1.2 Name, Role, Value",
                    "No violation",
                ],
            },
            {
                "type": "score",
                "instr": f"Rate the accessibility severity (0=no issue, 1=minor, 2=moderate, 3=significant, 4=critical)",
                "options": ["0", "1", "2", "3", "4"],
            },
        ],
    })
    
    return {
        "pattern": pattern_desc,
        "result": result,
    }


def main():
    # Example usage
    print("Kev-WCAG Example Usage")
    print("=" * 50)
    
    # Load model (replace with actual path after training)
    model_path = "model/kev-wcag"
    print(f"Loading model from: {model_path}")
    
    # Note: Model needs to be trained first before running this example
    print("\nTo use this example:")
    print("1. Run the Kaggle training notebook first")
    print("2. Save the trained model to model/kev-wcag/")
    print("3. Run this script")
    
    # Example HTML patterns to test
    examples = [
        {
            "desc": "Low contrast text",
            "html": '<p style="color: #ddd; background: white;">Hard to read text</p>',
        },
        {
            "desc": "Image without alt text",
            "html": '<img src="photo.jpg">',
        },
        {
            "desc": "Properly labeled input",
            "html": '<label for="email">Email</label><input type="email" id="email">',
        },
    ]
    
    print("\nExample patterns:")
    for i, ex in enumerate(examples, 1):
        print(f"{i}. {ex['desc']}")
        print(f"   HTML: {ex['html']}")
    
    print("\nSee evaluation/evaluate.py for full test suite")


if __name__ == "__main__":
    main()
