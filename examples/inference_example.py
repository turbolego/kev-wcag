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
        "questions": {
            "has_violation": {
                "type": "noul",
                "instructions": f"Does this HTML pattern have a WCAG accessibility violation? Pattern: {pattern_desc}",
                "label": None
            },
            "which_criterion": {
                "type": "choice",
                "instructions": f"Which WCAG 2.2 success criterion does this pattern violate? Pattern: {pattern_desc}",
                "criteria": {
                    "1.1.1 Non-text Content - Missing alt text or text alternatives": None,
                    "1.2.2 Captions - Missing captions for video/audio": None,
                    "1.2.5 Audio Description - Missing audio description": None,
                    "1.3.1 Info and Relationships - Missing semantic structure": None,
                    "1.4.3 Contrast - Insufficient color contrast": None,
                    "1.4.4 Resize - Text cannot be resized": None,
                    "2.1.1 Keyboard - Not keyboard accessible": None,
                    "2.4.1 Bypass Blocks - No skip link": None,
                    "2.4.4 Link Purpose - Non-descriptive link text": None,
                    "2.4.6 Headings - Missing/incorrect headings": None,
                    "2.4.7 Focus Visible - Missing focus indicator": None,
                    "2.5.8 Target Size - Touch target too small": None,
                    "3.1.1 Language - Missing lang attribute": None,
                    "4.1.2 Name Role Value - ARIA/semantic issues": None,
                    "3.3.2 Labels - Incorrect form labels": None,
                    "No WCAG 2.2 violation - this pattern is accessible": None,
                },
                "label": None
            },
            "severity": {
                "type": "score",
                "instructions": f"Rate the accessibility severity (0=no issue, 1=minor, 2=moderate, 3=significant, 4=critical). Pattern: {pattern_desc}",
                "criteria": [
                    "0: No accessibility issue",
                    "1: Minor issue, low impact",
                    "2: Moderate issue, affects some users",
                    "3: Significant issue, affects many users",
                    "4: Critical issue, blocks access entirely"
                ],
                "label": None
            },
            "is_accessible": {
                "type": "noul",
                "instructions": f"Is this HTML pattern fully accessible per WCAG 2.2? Pattern: {pattern_desc}",
                "label": None
            },
        },
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
