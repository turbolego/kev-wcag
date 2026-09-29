# Kev-WCAG

Kev model fine-tuned on WCAG 2.2 accessibility evaluation tasks.

## Status: Training Pipeline Ready

**Training notebook:** https://www.kaggle.com/code/hummern/wcag-kev-train

The training environment has been verified and the pipeline is ready, but the actual model training step was not completed in the Kaggle run. The notebook:
1. ✅ Successfully patched numpy 2.x compatibility for transformers 4.49.0
2. ✅ Successfully installed kev from GitHub (`pip install git+https://github.com/jaredpalmer/kev.git`)
3. ✅ Successfully imported kev and verified GPU access (Tesla T4)
4. ⚠️ Attempted to load Qwen2 model - import failed due to environment constraints
5. ❌ Did not execute actual fine-tuning training loop

## Dataset

**Source:** hummern/wcag-kev-training (Kaggle dataset)
**Size:** 200 synthetic WCAG 2.2 accessibility patterns
**Format:** JSONL with Kev-compatible record structure

### Pattern categories covered:
- Alt text violations (1.1.1)
- Label/form issues (4.1.2, 1.3.1, 3.3.2)
- Heading structure (2.4.6, 1.3.1)
- Link text (2.4.4)
- Color contrast (1.4.3)
- Landmarks (1.3.1)
- ARIA misuse (4.1.2)
- Keyboard accessibility (2.1.1)
- Focus indicators (2.4.7)
- Form grouping (1.3.1)
- Touch target size (2.5.8)
- Language declaration (3.1.1)
- Video captions (1.2.2)
- Table accessibility (1.3.1)
- Text resizing (1.4.4)
- Skip navigation (2.4.1)

### Record structure:
```json
{
  "state": "HTML pattern with description",
  "questions": [
    {"type": "noul", "instr": "...", "label": true/false},
    {"type": "choice", "instr": "...", "options": [...], "label": 0},
    {"type": "score", "instr": "...", "options": [...], "label": 3},
    {"type": "noul", "instr": "...", "label": false}
  ],
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

## How to train the model

```bash
# 1. Clone this repo
git clone https://github.com/turbolego/kev-wcag.git
cd kev-wcag

# 2. Install kev
pip install git+https://github.com/jaredpalmer/kev.git

# 3. Run the Kaggle notebook or local training script
# See training/kaggle_notebook.ipynb for the full training pipeline
# See training/train.py and training/model.py for the Kev training code

# 4. Expected training command (when running in Kev environment):
# from kev.model import AutoModelForCausalLM
# model = AutoModelForCausalLM.from_pretrained("jaredpalmer/kev-4b")
# model.train(data="data/wcag/wcag_train.jsonl", epochs=3, lr=2e-5)
# model.save("model/kev-wcag")
```

## How to use

### Prerequisites
```bash
pip install git+https://github.com/jaredpalmer/kev.git
```

### Basic inference (after model training)
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

## Test Results

### Evaluation Methodology

The test suite evaluates three capabilities:

| Test | Question Type | Metric |
|------|---------------|--------|
| Violation Detection | noul (yes/no) | Accuracy |
| Criterion Identification | choice | Accuracy |
| Severity Estimation | score | Accuracy (±1 tolerance) |

### Expected Comparison

| Model | Violation Detection | Criterion Identification | Severity Estimation |
|-------|---------------------|--------------------------|---------------------|
| Kev base (jaredpalmer/kev-4b) | TBD | TBD | TBD |
| Kev-WCAG (fine-tuned) | TBD | TBD | TBD |

*Results pending model training completion.*

## Repository Structure

```
kev-wcag/
├── data/
│   └── wcag/
│       └── wcag_train.jsonl    # Training data (200 examples)
├── model/                      # Trained model weights (will be added after training)
├── training/
│   ├── kaggle_notebook.ipynb   # Kaggle training kernel
│   ├── train.py                # Kev training script (from upstream kev)
│   └── model.py                # Kev model utilities (from upstream kev)
├── scripts/
│   └── generate_wcag_data.py   # Dataset generation script
├── evaluation/
│   └── results.md              # Test results (to be added after training)
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
- **Dataset:** https://www.kaggle.com/datasets/hummern/wcag-kev-training
