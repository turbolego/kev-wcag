# Kev-WCAG Training Guide

This guide walks through training a Kev model on WCAG 2.2 accessibility evaluation tasks.

## Prerequisites

- Kaggle account with GPU access (Tesla T4 recommended)
- GitHub account
- Python 3.12+ (locally)

## Quick Start

### Option 1: Run on Kaggle (Recommended)

1. Open the training notebook: https://www.kaggle.com/code/hummern/wcag-kev-train
2. Click "Copy and Edit" to create your own copy
3. Run all cells
4. The notebook will:
   - Patch numpy/transformers compatibility
   - Install kev
   - Load base model
   - Fine-tune on 200 WCAG patterns
   - Save trained model to `/tmp/kev-wcag-model/`

### Option 2: Run Locally

```bash
# Clone this repository
git clone https://github.com/turbolego/kev-wcag.git
cd kev-wcag

# Install dependencies
pip install git+https://github.com/jaredpalmer/kev.git
pip install torch transformers

# Run training
python training/train.py --data data/wcag/wcag_train.jsonl --out model/kev-wcag
```

## Training Process

### Step 1: Environment Setup

The notebook automatically patches compatibility issues between numpy 2.x and transformers 4.49.0. This is necessary because:

- Kaggle provides numpy 2.5.3 (newer than most model requirements)
- The Kev library uses transformers 4.49.0 which expects numpy < 2.1
- These patches add missing numpy attributes at runtime

### Step 2: Install Kev

```bash
pip install git+https://github.com/jaredpalmer/kev.git
```

Note: The PyPI package `kev` is unrelated (an ORM). Use the GitHub source.

### Step 3: Load Base Model

```python
from kev.model import AutoModelForCausalLM

# Try Qwen2 (works with this transformers version)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2-0.5B",  # or "Qwen/Qwen2-7B"
    trust_remote_code=True
)
```

### Step 4: Fine-tune on WCAG Data

```python
# Load dataset
import json
with open("data/wcag/wcag_train.jsonl") as f:
    records = [json.loads(line) for line in f]

# Fine-tune
model.train(
    data=records,
    epochs=3,
    lr=2e-5,
    batch_size=4,
    accumulation_steps=8,
)
```

### Step 5: Save Model

```python
model.save("model/kev-wcag")
```

## Evaluation

After training, evaluate the model:

```bash
python evaluation/evaluate.py --model model/kev-wcag --data data/wcag/wcag_train.jsonl
```

Compare with base model:

```bash
# Evaluate base model (no fine-tuning)
python evaluation/evaluate.py --model jaredpalmer/kev-4b --data data/wcag/wcag_train.jsonl
```

## Results Interpretation

The model outputs three types of answers:

1. **Violation detection** (noul): Yes/No whether the pattern has a WCAG violation
2. **Criterion identification** (choice): Which specific WCAG criterion is violated
3. **Severity estimation** (score): Rating 0-4 how severe the issue is

Metrics to track:
- Violation detection accuracy
- Criterion identification accuracy (exact match)
- Severity estimation accuracy (within ±1 tolerance)

## Troubleshooting

### Import errors with transformers

If you see errors like `ImportError: cannot import name 'split_attention_implementation'`, the notebook patches are needed. Make sure Cell 0 runs first.

### Kev import errors

If `import kev` fails, verify you installed from GitHub:
```bash
pip install git+https://github.com/jaredpalmer/kev.git
```

### Model loading errors

If Qwen2 models fail to load, try:
- Smaller model: `Qwen/Qwen2-0.5B` instead of `Qwen/Qwen2-7B`
- Check that `trust_remote_code=True` is set
- Ensure you have enough VRAM (T4 has 16GB)

## Publishing Your Model

After training, you can:

1. Upload to HuggingFace Hub:
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model.push_to_hub("your-username/kev-wcag")
tokenizer.push_to_hub("your-username/kev-wcag")
```

2. Share on Kaggle:
- Upload the model directory as a dataset
- Link to your notebook with training instructions

## References

- [Kev GitHub](https://github.com/jaredpalmer/kev)
- [Kaggle Training Notebook](https://www.kaggle.com/code/hummern/wcag-kev-train)
- [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
