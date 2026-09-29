#!/usr/bin/env python3
"""Generate Kev-formatted training data from WCAG 2.2 knowledge.

Creates records for:
- noul: "Does this HTML pattern have a WCAG violation?"
- choice: "Which WCAG success criterion does this violate?"
- score: "Rate the accessibility severity of this pattern (0-4)"

Uses wcag_22.json and wcag-skill knowledge as source material.
"""
import json
import random
from pathlib import Path

# Load WCAG 2.2 spec
with open("/home/kloa/repos/AI-WCAG-Gauntlet/resources/wcag_22.json") as f:
    wcag_spec = json.load(f)

# HTML5 tags from the benchmark
with open("/home/kloa/repos/AI-WCAG-Gauntlet/resources/html_tags.json") as f:
    html_tags_data = json.load(f)
HTML_TAGS = html_tags_data["tags"]

# Common accessibility patterns and their violation status
# Each entry: (pattern_description, state_html, has_violation, violated_criteria, severity, fix_hint)
WCAG_PATTERNS = [
    # Alt text violations
    (
        "Image without alt attribute",
        '<img src="photo.jpg">',
        True,
        ["1.1.1"],
        4,
        "Add alt='description' or alt='' for decorative images"
    ),
    (
        "Image with empty alt (decorative - correct)",
        '<img src="decoration.png" alt="">',
        False,
        [],
        0,
        "Empty alt is correct for decorative images"
    ),
    (
        "Image with descriptive alt text",
        '<img src="chart.png" alt="Sales growth chart showing 20% increase">',
        False,
        [],
        0,
        "Descriptive alt text is correct"
    ),
    (
        "Input without label",
        '<input type="text" name="email">',
        True,
        ["4.1.2", "1.3.1"],
        4,
        "Add <label for='id'> or aria-label"
    ),
    (
        "Input with proper label",
        '<label for="email">Email</label><input type="email" id="email" name="email">',
        False,
        [],
        0,
        "Proper label association is correct"
    ),
    # Heading structure
    (
        "Skipping heading levels (h1 to h3)",
        '<h1>Main Title</h1><H3>Subsection</h3>',
        True,
        ["1.3.1", "2.4.6"],
        3,
        "Use sequential headings: h1 → h2 → h3"
    ),
    (
        "Correct heading hierarchy",
        '<h1>Main</h1><h2>Section</h2><h3>Subsection</h3>',
        False,
        [],
        0,
        "Sequential heading levels are correct"
    ),
    # Link text
    (
        "Non-descriptive link text 'click here'",
        '<a href="/docs">click here</a> to read the docs',
        True,
        ["2.4.4"],
        2,
        "Use descriptive link text: 'Read the documentation'"
    ),
    (
        "Descriptive link text",
        '<a href="/docs">Read the documentation</a>',
        False,
        [],
        0,
        "Descriptive link text is correct"
    ),
    # Color contrast
    (
        "Low contrast text (light gray on white)",
        '<p style="color: #ddd; background: white;">Hard to read text</p>',
        True,
        ["1.4.3"],
        3,
        "Ensure contrast ratio ≥ 4.5:1 for normal text"
    ),
    (
        "Good contrast text (black on white)",
        '<p style="color: #000; background: white;">Readable text</p>',
        False,
        [],
        0,
        "High contrast is correct"
    ),
    # Landmarks
    (
        "Missing main landmark",
        '<div><h1>Page Title</h1><p>Content here</p></div>',
        True,
        ["1.3.1"],
        3,
        "Wrap content in <main> landmark"
    ),
    (
        "Proper landmark structure",
        '<header><nav>...</nav></header><main><h1>Title</h1><p>Content</p></main><footer>...</footer>',
        False,
        [],
        0,
        "Proper landmarks are correct"
    ),
    # ARIA misuse
    (
        "ARIA role on semantic element (redundant)",
        '<button role="button">Click me</button>',
        True,
        ["4.1.2"],
        2,
        "Don't add role to elements that already have it"
    ),
    (
        "Correct ARIA usage",
        '<div role="alert" aria-live="assertive">Error occurred</div>',
        False,
        [],
        0,
        "Proper ARIA usage is correct"
    ),
    # Keyboard accessibility
    (
        "Click event without keyboard support",
        '<div onclick="handleSubmit()">Submit</div>',
        True,
        ["2.1.1", "4.1.2"],
        4,
        "Use <button> or add keyboard event handler"
    ),
    (
        "Button with keyboard support",
        '<button onclick="handleSubmit()">Submit</button>',
        False,
        [],
        0,
        "Native button has built-in keyboard support"
    ),
    # Focus indicators
    (
        "Removed focus outline",
        '<style>a:focus { outline: none; }</style><a href="#">Link</a>',
        True,
        ["2.4.7"],
        3,
        "Provide visible focus indicator"
    ),
    (
        "Visible focus indicator",
        '<style>a:focus { outline: 2px solid blue; }</style><a href="#">Link</a>',
        False,
        [],
        0,
        "Visible focus indicator is correct"
    ),
    # Form grouping
    (
        "Unlabeled form fields without fieldset",
        '<form><input type="radio" name="opt">Option 1<br><input type="radio" name="opt">Option 2</form>',
        True,
        ["1.3.1"],
        3,
        "Wrap radio buttons in <fieldset> with <legend>"
    ),
    (
        "Proper form field grouping",
        '<form><fieldset><legend>Choose option</legend><input type="radio" name="opt">Option 1</fieldset></form>',
        False,
        [],
        0,
        "Proper fieldset grouping is correct"
    ),
    # Touch targets
    (
        "Small touch target (under 24px)",
        '<style>.btn { width: 10px; height: 10px; }</style><button class="btn">X</button>',
        True,
        ["2.5.8"],
        2,
        "Ensure touch targets are at least 24×24px"
    ),
    (
        "Adequate touch target size",
        '<style>.btn { min-height: 24px; min-width: 24px; }</style><button class="btn">Submit</button>',
        False,
        [],
        0,
        "Adequate touch target size is correct"
    ),
    # Language declaration
    (
        "Missing lang attribute on html",
        '<html><head><title>Page</title></head><body>Content</body></html>',
        True,
        ["3.1.1"],
        3,
        "Add lang attribute: <html lang='en'>"
    ),
    (
        "Proper language declaration",
        '<html lang="en"><head><title>Page</title></head><body>Content</body></html>',
        False,
        [],
        0,
        "Language declaration is correct"
    ),
    # Video captions
    (
        "Video without captions",
        '<video src="video.mp4" controls></video>',
        True,
        ["1.2.2"],
        4,
        "Add <track kind='captions'> for video"
    ),
    (
        "Video with captions",
        '<video src="video.mp4" controls><track kind="captions" src="captions.vtt" srclang="en" label="English"></video>',
        False,
        [],
        0,
        "Video with captions is correct"
    ),
    # Table accessibility
    (
        "Table without header association",
        '<table><tr><td>Row 1 Col 1</td><td>Row 1 Col 2</td></tr></table>',
        True,
        ["1.3.1"],
        2,
        "Use <th> with scope attribute for data tables"
    ),
    (
        "Accessible data table",
        '<table><thead><tr><th scope="col">Name</th><th scope="col">Value</th></tr></thead><tbody><tr><td>A</td><td>1</td></tr></tbody></table>',
        False,
        [],
        0,
        "Proper table headers are correct"
    ),
    # Text resizing
    (
        "Fixed size text that prevents resizing",
        '<p style="font-size: 12px; !important;">Text that cannot resize</p>',
        True,
        ["1.4.4"],
        2,
        "Use relative units (em, rem) and avoid !important on font-size"
    ),
    (
        "Resizable text with relative units",
        '<p style="font-size: 1rem;">Text that can resize</p>',
        False,
        [],
        0,
        "Relative units allow text resizing"
    ),
    # Bypass mechanism
    (
        "No skip link for repeated content",
        '<header><nav>...long nav...</nav></header><main>Content</main>',
        True,
        ["2.4.1"],
        2,
        "Add skip link: <a href='#main'>Skip to content</a>"
    ),
    (
        "Proper skip link",
        '<header><a href="#main">Skip to content</a><nav>...</nav></header><main id="main">Content</main>',
        False,
        [],
        0,
        "Skip link is correct"
    ),
    # Audio descriptions
    (
        "Video without audio description track",
        '<video src="video.mp4" controls><track kind="captions" src="subs.vtt"></video>',
        True,
        ["1.2.5"],
        3,
        "Add audio description or media alternative"
    ),
    # Multiple labels
    (
        "Multiple labels for one input",
        '<label for="f1">First</label><label for="f1">Second</label><input id="f1" type="text">',
        True,
        ["4.1.2", "3.3.2"],
        2,
        "Each input should have exactly one label"
    ),
]

def make_state_html(pattern_desc: str, html: str) -> str:
    """Create a state string for the record (must be a string for kev.model.encode)."""
    return f"""Identify accessibility issues in this HTML pattern.

Pattern: {pattern_desc}

HTML:
{html}
"""

def generate_records(n: int = 200, seed: int = 42) -> list:
    """Generate Kev-formatted training records."""
    rng = random.Random(seed)
    records = []
    
    # Repeat patterns to reach desired count
    repeats = (n + len(WCAG_PATTERNS) - 1) // len(WCAG_PATTERNS)
    
    for _ in range(repeats):
        rng.shuffle(WCAG_PATTERNS)
        for pattern_desc, html, has_violation, violated_criteria, severity, fix_hint in WCAG_PATTERNS:
            if len(records) >= n:
                break
            
            state = make_state_html(pattern_desc, html)
            
            # Determine criteria names from WCAG spec
            criteria_names = []
            for crit_id in violated_criteria:
                for guideline in wcag_spec:
                    for sc in guideline.get("success_criteria", []):
                        if sc["ref_id"] == crit_id:
                            criteria_names.append(f"{crit_id}: {sc['title']}")
                            break
            
            criteria_text = "; ".join(criteria_names) if criteria_names else "None"
            
            # Build questions
            questions = {}
            
            # Question 1: Does this have a violation? (noul)
            questions["has_violation"] = {
                "type": "noul",
                "instr": f"Does this HTML pattern have a WCAG accessibility violation? Pattern: {pattern_desc}",
                "options": [],
                "label": has_violation,
                "src": "wcag_pattern"
            }
            
            # Question 2: Which criteria? (choice) - only when there's a violation
            if has_violation:
                option_list = [
                    "1.1.1 Non-text Content - Missing alt text or text alternatives",
                    "1.2.2 Captions - Missing captions for video/audio",
                    "1.2.5 Audio Description - Missing audio description",
                    "1.3.1 Info and Relationships - Missing semantic structure",
                    "1.4.3 Contrast - Insufficient color contrast",
                    "1.4.4 Resize - Text cannot be resized",
                    "2.1.1 Keyboard - Not keyboard accessible",
                    "2.4.1 Bypass Blocks - No skip link",
                    "2.4.4 Link Purpose - Non-descriptive link text",
                    "2.4.6 Headings - Missing/incorrect headings",
                    "2.4.7 Focus Visible - Missing focus indicator",
                    "2.5.8 Target Size - Touch target too small",
                    "3.1.1 Language - Missing lang attribute",
                    "4.1.2 Name Role Value - ARIA/semantic issues",
                    "3.3.2 Labels - Incorrect form labels"
                ]
                # Find indices of violated criteria
                label_idx = 0
                for idx, opt in enumerate(option_list):
                    crit_id = opt.split(".")[0] + "." + opt.split(".")[1]
                    if crit_id in violated_criteria:
                        label_idx = idx
                        break
                
                questions["which_criterion"] = {
                    "type": "choice",
                    "instr": f"Which WCAG 2.2 success criterion does this pattern violate? Pattern: {pattern_desc}",
                    "options": option_list,
                    "label": label_idx,
                    "src": "wcag_criterion"
                }
            else:
                questions["which_criterion"] = {
                    "type": "choice",
                    "instr": f"Does this HTML pattern violate any WCAG 2.2 success criteria? Pattern: {pattern_desc}",
                    "options": [
                        "No WCAG 2.2 violation - this pattern is accessible",
                        "Some other issue not listed"
                    ],
                    "label": 0,
                    "src": "wcag_criterion"
                }
            
            # Question 3: Severity rating (score)
            questions["severity"] = {
                "type": "score",
                "instr": f"Rate the accessibility severity of this pattern (0=no issue, 1=minor, 2=moderate, 3=significant, 4=critical). Pattern: {pattern_desc}",
                "options": [
                    "0: No accessibility issue",
                    "1: Minor issue, low impact",
                    "2: Moderate issue, affects some users",
                    "3: Significant issue, affects many users",
                    "4: Critical issue, blocks access entirely"
                ],
                "label": severity,
                "src": "wcag_severity"
            }
            
            # Question 4: Is this pattern accessible? (noul - inverted)
            questions["is_accessible"] = {
                "type": "noul",
                "instr": f"Is this HTML pattern fully accessible per WCAG 2.2? Pattern: {pattern_desc}",
                "options": [],
                "label": not has_violation,
                "src": "wcag_accessible"
            }
            
            record = {
                "state": state,
                "questions": list(questions.values()),
                "_meta": {
                    "source": "wcag_pattern",
                    "pattern": pattern_desc,
                    "has_violation": has_violation,
                    "violated_criteria": violated_criteria,
                    "severity": severity,
                    "fix_hint": fix_hint,
                    "id": f"wcag_{len(records)}"
                }
            }
            records.append(record)
    
    return records

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate WCAG training data for Kev")
    parser.add_argument("--n", type=int, default=200, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out", type=str, default="wcag_train.jsonl", help="Output file")
    args = parser.parse_args()
    
    records = generate_records(n=args.n, seed=args.seed)
    
    output_path = Path(args.out)
    output_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n")
    
    print(f"Generated {len(records)} records to {output_path}")
    
    # Print stats
    violations = sum(1 for r in records if r["questions"][0]["label"])
    print(f"  With violations: {violations}")
    print(f"  Accessible: {len(records) - violations}")

    # Severity distribution
    sev_counts = {}
    for r in records:
        s = r["questions"][2]["label"]
        sev_counts[s] = sev_counts.get(s, 0) + 1
    print(f"  Severity distribution: {dict(sorted(sev_counts.items()))}")

if __name__ == "__main__":
    main()
