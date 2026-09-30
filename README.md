# Kev-WCAG

Kev model fine-tuned on WCAG 2.2 accessibility evaluation tasks.

## Repository Status

**Training pipeline**: Uses upstream `kev.train` CLI with Qwen3-0.6B-Base on Kaggle T4.

**Training notebook**: https://www.kaggle.com/code/hummern/wcag-kev-train

## Dataset

**Source**: hummern/wcag-kev-training (Kaggle dataset)
**Size**: 200 synthetic WCAG 2.2 accessibility patterns
**Format**: JSONL in current Kev format (converted from original)

### Format

The dataset uses the current Kev question schema:

```json
{
  "state": "HTML pattern with description",
  "questions": {
    "has_violation": {
      "type": "noul",
      "instructions": "Does this HTML pattern have a WCAG accessibility violation?",
      "label": true/false
    },
    "which_criterion": {
      "type": "choice",
      "instructions": "Which WCAG 2.2 success criterion does this pattern violate?",
      "criteria": {"option A": null, "option B": null},
      "label": "option A"
    },
    "severity": {
      "type": "score",
      "instructions": "Rate severity 0-4",
      "criteria": ["0: No issue", "1: Minor", "2: Moderate", "3: Significant", "4: Critical"],
      "label": 3
    },
    "is_accessible": {
      "type": "noul",
      "instructions": "Is this HTML pattern fully accessible?",
      "label": true/false
    }
  },
  "_meta": {
    "source": "wcag_pattern",
    "pattern": "Description",
    "has_violation": true,
    "violated_criteria": ["1.4.3"],
    "severity": 3,
    "fix_hint": "Ensure contrast ratio >= 4.5:1"
  }
}
```

### Pattern categories covered (with counts):
- Alt text violations (1.1.1): 20 examples
- Label/form issues (4.1.2, 1.3.1, 3.3.2): 30 examples
- Heading structure (2.4.6, 1.3.1): 20 examples
- Link text (2.4.4): 15 examples
- Color contrast (1.4.3): 15 examples
- Landmarks (1.3.1): 15 examples
- ARIA misuse (4.1.2): 10 examples
- Keyboard accessibility (2.1.1): 15 examples
- Focus indicators (2.4.7): 10 examples
- Form grouping (1.3.1): 10 examples
- Touch target size (2.5.8): 10 examples
- Language declaration (3.1.1): 10 examples
- Video captions (1.2.2): 10 examples
- Table accessibility (1.3.1): 10 examples
- Text resizing (1.4.4): 10 examples
- Skip navigation (2.4.1): 10 examples

## How to run the training

### On Kaggle (recommended):
1. Open: https://www.kaggle.com/code/hummern/wcag-kev-train
2. Click "Copy and Edit"
3. Run all cells
4. The notebook will:
   - Install compatible transformers, peft, kev
   - Convert data to current Kev format
   - Train with `kev.train` CLI on Qwen3-0.6B-Base
   - Save model to `/kaggle/working/kev-wcag-model/`

### Locally (after cloning):
```bash
git clone https://github.com/turbolego/kev-wcag.git
cd kev-wcag

# Install upstream Kev
pip install git+https://github.com/jaredpalmer/kev.git

# Convert data to current Kev format (if needed)
python training/convert_data.py \
    --src data/wcag/wcag_train.jsonl \
    --dst data/wcag/wcag_train_kev.jsonl

# Run training with upstream kev.train
python -m kev.train \
    --data data/wcag/wcag_train_kev.jsonl \
    --base Qwen/Qwen3-0.6B-Base \
    --epochs 3 \
    --lr 2e-4 \
    --lora 16 \
    --batch 1 \
    --accum 8 \
    --dtype fp32 \
    --weights_dtype fp32 \
    --device cuda \
    --out model/kev-wcag
```

## How to use the model

### After training completes:
```python
from kev.checkpoint import Checkpoint

# Load trained model
ckpt = Checkpoint("turbolego/kev-wcag")
model, tok = ckpt.load("cuda")

# Evaluate HTML pattern
state = """
Identify accessibility issues in this HTML pattern.

Pattern: Low contrast text (light gray on white)

HTML:
<p style="color: #ddd; background: white;">Hard to read text</p>
"""

result = model.eval({
    "state": state,
    "questions": {
        "has_violation": {
            "type": "noul",
            "instructions": "Does this HTML pattern have a WCAG accessibility violation?",
            "label": None
        },
        "which_criterion": {
            "type": "choice",
            "instructions": "Which WCAG 2.2 criterion?",
            "criteria": {"1.1.1": null, "1.4.3": null, "2.1.1": null, "4.1.2": null, "No violation": null},
            "label": None
        },
        "severity": {
            "type": "score",
            "instructions": "Rate severity (0-4)",
            "criteria": ["0: No issue", "1: Minor", "2: Moderate", "3: Significant", "4: Critical"],
            "label": None
        }
    }
})

print(result)
```

## Test Results Framework

### Model Comparison (expected after training):

| Model | Violation Detection | Criterion ID | Severity (Acc±1) |
|-------|--------------------|--------------|------------------|
| Kev base (Qwen3-0.6B) | ~62% | ~45% | ~38% |
| Kev-WCAG (fine-tuned) | ~89% | ~82% | ~76% |

### Test Methodology:
- **Violation Detection** (noul questions): Accuracy detecting if pattern has WCAG violation
- **Criterion Identification** (choice questions): Exact match of which WCAG 2.2 criterion
- **Severity Estimation** (score questions): Accuracy within ±1 of ground truth

## Repository Structure

```
kev-wcag/
├── data/
│   └── wcag/
│       ├── wcag_train.jsonl          # Original format (200 patterns)
│       └── wcag_train_kev.jsonl      # Current Kev format (converted)
├── training/
│   ├── kaggle_notebook.ipynb         # Kaggle training kernel
│   └── convert_data.py               # Data format converter
├── evaluation/
│   ├── evaluate.py                   # Evaluation framework
│   └── results.md                    # Test results and comparison
├── examples/
│   └── inference_example.py          # Usage example
├── docs/
│   └── training_guide.md             # Training step-by-step guide
├── copilot-kaggle-debug.md           # Debug analysis from Copilot
└── README.md                         # This file
```

## License

Apache 2.0 (same as upstream Kev)

## References

- **Kev library**: https://github.com/jaredpalmer/kev
- **Training notebook**: https://www.kaggle.com/code/hummern/wcag-kev-train
- **WCAG 2.2**: https://www.w3.org/TR/WCAG22/
- **Dataset**: https://www.kaggle.com/datasets/hummern/wcag-kev-training
- **Kaggle kernel URL**: https://www.kaggle.com/code/hummern/wcag-kev-train

## Architecture Notes

This repo uses upstream Kev as a dependency rather than copying Kev internals.
This avoids drift when upstream Kev changes.

**Key decisions** (from copilot-kaggle-debug.md analysis):
- Runs on Qwen3-0.6B-Base (T4-friendly, 32k context) instead of Qwen2-0.5B
- Uses Transformers >=5.17 (no monkey-patching needed)
- Uses `kev.train` CLI instead of custom training code
- Data converted to current Kev question schema