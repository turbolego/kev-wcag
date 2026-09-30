I dug through the current kev-wcag repo, the Kaggle notebook, and upstream Kev. The Qwen2 import failure is a symptom of a dependency/version mismatch, and there are a few additional problems that will hit immediately after that one.

What is actually going wrong

Your Kaggle notebook currently does this:

# notebook
# Transformers environment is 4.49.0
...
pip install git+https://github.com/jaredpalmer/kev.git
...
for mn in ['Qwen/Qwen2-0.5B','Qwen/Qwen2-7B']:
    m = kev.model.AutoModelForCausalLM.from_pretrained(...)

The important part is that the notebook is trying to make a newer Kev work inside a Transformers 4.49.0 environment by patching transformers internals. Your own notebook explicitly patches generic.py, import_utils.py, and auto_docstring.py before importing Kev.

That is the wrong direction.

The upstream Kev revision that produced the original 0.5B model requires:

transformers >=4.51,<4.58
peft >=0.15
torch >=2.6,<2.9
numpy >=2.5.3

and its actual base model is Qwen/Qwen2.5-0.5B, not Qwen/Qwen2-0.5B.

The current upstream Kev has moved on again and now requires:

transformers >=5.17,<6
peft >=0.21
torch >=2.6,<2.9
numpy >=2.5.3

and uses Qwen3.5/Qwen3.8 for the current generation.

So your notebook is effectively doing:

Kaggle Transformers 4.49
        ↓
monkey patches
        ↓
latest Kev main
        ↓
Qwen2 test model

Those components were never a coherent supported environment.

Qwen2 itself is not the problem

Current Transformers does support Qwen2ForCausalLM, and Qwen/Qwen2-0.5B is still present in the Transformers test suite.

The problem is that Kev wasn't designed around that checkpoint.

The original Kev-0.5B checkpoint was trained on:

Qwen/Qwen2.5-0.5B

with a 896-dimensional hidden representation.

Your Kaggle notebook instead tests:

Qwen/Qwen2-0.5B
Qwen/Qwen2-7B

So even getting Qwen2 to import would not make this the intended Kev training setup.

There is an even bigger inconsistency in your repository

Your README says:

from kev.model import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("jaredpalmer/kev-4b")

but your actual copied training/train.py defaults to:

--base Qwen/Qwen3-0.6B-Base

and constructs:

DecisionModel(a.base, ...)

Your training/model.py also loads the base through Hugging Face's AutoModelForCausalLM.

That means the README, Kaggle notebook, and training code are from different generations of Kev.

The current upstream trainer itself now defaults to Qwen/Qwen3-0.6B-Base.

I would stop patching Transformers entirely

The clean Kaggle strategy is:

Python 3.12
    ↓
supported Transformers
    ↓
single pinned Kev version
    ↓
Qwen3-0.6B-Base
    ↓
your WCAG data

For a Tesla T4, I'd use Qwen3-0.6B-Base, rather than jumping to Qwen3.5-4B/9B. The current upstream Qwen3-0.6B setup is specifically documented and the model has a 32,768-token base context.

Recommended replacement for your Kaggle setup

Delete the huge Transformer monkey-patching cell.

Use this instead:

# Clean Kaggle environment for Kev + Qwen3-0.6B

!pip install -q -U \
    "numpy>=2.5.3,<3" \
    "transformers>=5.17,<6" \
    "peft>=0.21" \
    "accelerate>=1.15" \
    "datasets>=3.0" \
    "scikit-learn>=1.9.1"

!pip install -q \
    "git+https://github.com/jaredpalmer/kev.git"

import sys
import torch
import numpy
import transformers
import peft
import kev

print("Python:", sys.version)
print("PyTorch:", torch.__version__)
print("NumPy:", numpy.__version__)
print("Transformers:", transformers.__version__)
print("PEFT:", peft.__version__)
print("Kev:", kev.__file__)
print("CUDA:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

Do not add trust_remote_code=True as a workaround. Qwen2/Qwen3 are natively supported by Transformers.

Then test the exact backbone:

from transformers import AutoTokenizer, AutoModelForCausalLM

BASE = "Qwen/Qwen3-0.6B-Base"

tokenizer = AutoTokenizer.from_pretrained(BASE)

model = AutoModelForCausalLM.from_pretrained(
    BASE,
    dtype=torch.float32,
    attn_implementation="sdpa",
)

print(type(model).__name__)
print("hidden size:", model.config.hidden_size)
print("model type:", model.config.model_type)

del model
torch.cuda.empty_cache()

The Qwen3-0.6B config identifies itself as model_type: "qwen3" and Qwen3ForCausalLM.

One more blocker: your WCAG JSON isn't in the current Kev input format

Your data currently looks like:

{
  "state": "...",
  "questions": [
    {
      "type": "choice",
      "instr": "...",
      "options": ["...", "..."],
      "label": 0
    }
  ]
}

That's the old/internal representation used by your copied training code.

Current Kev's --data loader expects:

{
  "state": "...",
  "questions": {
    "which_criterion": {
      "type": "choice",
      "instructions": "...",
      "criteria": {
        "option A": null,
        "option B": null
      },
      "label": "option A"
    }
  }
}

with instructions, criteria, and a keyed question object.

So once the model-import issue is fixed, feeding your current wcag_train.jsonl directly into current kev.train --data will fail too.

The conversion is straightforward

I would add a preprocessing step like this:

import json
from pathlib import Path

src = Path("/kaggle/input/wcag-kev-training/wcag_train.jsonl")
dst = Path("/kaggle/working/wcag_train_kev.jsonl")

with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
    for line in fin:
        record = json.loads(line)

        questions = {}

        for i, q in enumerate(record["questions"]):
            if q["type"] == "noul":
                questions["has_violation" if i == 0 else "is_accessible"] = {
                    "type": "noul",
                    "instructions": q["instr"],
                    "label": bool(q["label"]),
                }

            elif q["type"] == "choice":
                questions["which_criterion"] = {
                    "type": "choice",
                    "instructions": q["instr"],
                    "criteria": {option: None for option in q["options"]},
                    "label": q["options"][q["label"]],
                }

            elif q["type"] == "score":
                questions["severity"] = {
                    "type": "score",
                    "instructions": q["instr"],
                    "criteria": q["options"],
                    "label": int(q["label"]),
                }

        converted = {
            "state": record["state"],
            "questions": questions,
            "_meta": record.get("_meta", {}),
        }

        fout.write(json.dumps(converted, ensure_ascii=False) + "\n")

print(dst)

Then the T4-friendly training invocation can be:

python -m kev.train \
  --data /kaggle/working/wcag_train_kev.jsonl \
  --base Qwen/Qwen3-0.6B-Base \
  --epochs 3 \
  --lr 2e-4 \
  --lora 16 \
  --batch 1 \
  --accum 8 \
  --dtype fp32 \
  --weights_dtype fp32 \
  --device cuda \
  --out /kaggle/working/kev-wcag

The current Kev trainer explicitly supports custom --data, --base, --batch, --accum, --dtype, and --device settings.

There is one more repository problem

Your training/train.py imports:

from .checkpoint import Checkpoint, Meta, write_meta
from .device import ...
from .data import ...
from .suite import ...

but your training/ directory, according to the repository itself, only contains:

kaggle_notebook.ipynb
train.py
model.py

So that copied training/train.py cannot function as a self-contained training package from the GitHub repo. The README currently overstates the state of the training pipeline.

My recommended architecture for kev-wcag

I'd simplify the repo substantially:

kev-wcag/
├── data/
│   └── wcag/
│       ├── wcag_train.jsonl          # your source format
│       └── wcag_train_kev.jsonl      # generated Kev format
├── training/
│   ├── kaggle_notebook.ipynb
│   └── convert_data.py
├── evaluation/
│   └── ...
└── README.md

and let upstream kev.train do the actual training, rather than copying pieces of Kev into training/.

That avoids exactly the problem you're hitting now: upstream Kev changes while the copied model.py, copied train.py, notebook, and README quietly drift apart.

One particularly important point: the current upstream project has already moved from the Qwen3 generation to Qwen3.5/Qwen3.8, while explicitly retaining the older Qwen3 models as a previous generation. For your Kaggle T4 WCAG experiment, Qwen3-0.6B is the cleanest compatibility target rather than trying to resurrect the Qwen2 path.

So the immediate diagnosis is:

Transformers 4.49 + monkey patches + moving Kev main + Qwen2 is the broken combination. Replace it with a coherent Qwen3/Transformers environment and convert the WCAG dataset to the current Kev schema.
