# Kev-WCAG

Kev model fine-tuned on WCAG 2.2 accessibility evaluation tasks. Trained on 200 synthetic accessibility patterns covering contrast, semantic structure, keyboard accessibility, forms, ARIA, and more.

## What's in this repo

```
data/wcag/wcag_train.jsonl    # 200 training examples (JSONL)
training/kaggle_notebook.ipynb # Kaggle kernel that ran the training
training/train.py              # Kev training script (from upstream kev)
training/model.py              # Kev model utilities (from upstream kev)
scripts/generate_wcag_data.py  # Script that generated the WCAG dataset
docs/README.md                 # Full documentation
evaluation/                    # Test scripts and results
examples/                      # Usage examples
```

## Dataset

200 synthetic WCAG accessibility patterns covering:

- **Contrast violations** (1.4.3)
- **Semantic structure issues** (1.3.1, 2.4.6)
- **Keyboard accessibility** (2.1.1, 2.4.7)
- **Form/label issues** (3.3.2)
- **ARIA/semantic issues** (4.1.2)
- **Other common WCAG 2.2 violations**

Each example has:
- `state`: HTML pattern description
- `questions`: 4 questions (violation detection, criterion identification, severity scoring, accessible check)
- `_meta`: ground truth (violation status, criteria, severity, fix hint)

## How it was trained

The model was trained on Kaggle using the Kev library with WCAG accessibility evaluation data.

**Training environment:**
- GPU: Tesla T4 (Kaggle)
- Framework: Kev (jaredpalmer/kev) + PyTorch 2.8.0
- Base model: Qwen2-0.5B / Qwen2-7B

**Training notebook:** https://www.kaggle.com/code/hummern/wcag-kev-train

**Key training steps:**
1. Patch numpy 2.x compatibility for transformers 4.49.0
2. Install kev from GitHub: `pip install git+https://github.com/jaredpalmer/kev.git`
3. Load base model (Qwen2)
4. Fine-tune on 200 WCAG examples
5. Evaluate on held-out accessibility patterns

## How to use

### Prerequisites

```bash
pip install git+https://github.com/jaredpalmer/kev.git
```

### Run inference

```python
from kev.model import AutoModelForCausalLM

# Load the trained model
model = AutoModelForCausalLM.from_pretrained("turbolego/kev-wcag")

# Evaluate an HTML pattern
state = """
Identify accessibility issues in this HTML pattern.

Pattern: Low contrast text (light gray on white)

HTML:
<p style="color: #ddd; background: white;">Hard to read text</p>
"""

result = model.eval({
    "state": state,
    "questions": [
        {"type": "noul", "instr": "Does this HTML pattern have a WCAG accessibility violation?"},
        {"type": "choice", "instr": "Which WCAG 2.2 success criterion does this pattern violate?", 
         "options": ["1.1.1", "1.4.3", "2.1.1", "4.1.2"]},
        {"type": "score", "instr": "Rate the accessibility severity (0-4)"},
    ]
})

print(result)
```

### Using the dataset

```python
import json

with open("data/wcag/wcag_train.jsonl") as f:
    for line in f:
        example = json.loads(line)
        print(f"Pattern: {example['_meta']['pattern']}")
        print(f"Has violation: {example['_meta']['has_violation']}")
        print(f"Severity: {example['_meta']['severity']}")
        print(f"Fix: {example['_meta']['fix_hint']}")
```

## Test results

### WCAG violation detection accuracy

| Model | Violation Detection | Criterion Identification | Severity Estimation |
|-------|---------------------|--------------------------|---------------------|
| Kev base (no WCAG training) | --% | --% | --% |
| Kev-WCAG (this model) | --% | --% | --% |

### Sample predictions

```
Pattern: Low contrast text (light gray on white)
Expected: Violation (1.4.3 Contrast), Severity 3
```

See `evaluation/results.md` for full test details.

## Repository structure

```
kev-wcag/
├── data/
│   └── wcag/
│       └── wcag_train.jsonl    # Training data (200 examples)
├── training/
│   ├── kaggle_notebook.ipynb   # Kaggle training kernel
│   ├── train.py                # Kev training script
│   └── model.py                # Model utilities
├── scripts/
│   └── generate_wcag_data.py   # Dataset generation script
├── evaluation/
│   └── results.md              # Test results and comparison
├── examples/
│   └── inference_example.py    # Example usage
└── README.md
```

## License

Apache 2.0 (same as upstream Kev)

## References

- **Kev library:** https://github.com/jaredpalmer/kev
- **Training notebook:** https://www.kaggle.com/code/hummern/wcag-kev-train
- **WCAG 2.2:** https://www.w3.org/TR/WCAG22/
