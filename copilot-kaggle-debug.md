I inspected the attached wcag_train_kev.jsonl, and it tells us something important.

The conversion itself succeeded

The file contains exactly 200 valid JSONL records. Every record has the expected top-level structure:

state
questions
_meta

and the questions have the expected Kev-style fields (type, instructions, label, and criteria where applicable). For example, the first records correctly encode a non-violation as false / None / 0, while the image-without-alt example is true / 1.1.1 / 4. 

So the Qwen/Kev import problem is definitely behind us: the notebook successfully produced a dataset in the format it intended to feed into Kev.

But I see a significant dataset-quality problem

The 200 examples are not 200 unique WCAG examples.

There are only 20 unique _meta.pattern values, repeated to make 200 records.

For example:

Image without alt → 11 copies

Missing lang → 12 copies

Has label → 19 copies

Has lang → 16 copies

Image with alt → 17 copies

Link no text → 13 copies


And each repeated pattern has identical labels.

For instance, every Image without alt record is:

has_violation = true
criterion     = 1.1.1
severity      = 4

The examples are therefore effectively duplicated training samples rather than independent WCAG cases. The attached file shows this repetition throughout the dataset.  

Distribution

I counted:

Label	Count

No violation	109
Violation	91
Severity 0	109
Severity 2	36
Severity 3	34
Severity 4	21


There are no severity 1 examples.

The criterion distribution is also very small:

WCAG criterion	Count

None	109
1.3.1	33
2.4.4	13
3.1.1	12
1.1.1	11
2.4.7	9
1.4.3	8
4.1.2	5


This changes my assessment of the Kaggle run

If the Kaggle notebook successfully trained on this file, then:

Yes, it probably did perform a technically valid training run.

But:

No, I would not yet consider it a successful WCAG-trained Kev model.

The reason is not the Qwen2/Kev import issue anymore. The bigger issue is that the training set is essentially:

20 synthetic WCAG patterns
×
repeated examples
=
200 records

That makes it very easy for a small model to memorize the training patterns.

For example, the model could learn:

<img src="photo.jpg">
→ violation
→ 1.1.1
→ severity 4

without learning the more general accessibility reasoning you actually want Kev to learn.

The same applies to <input> without a label, empty buttons, empty headings, missing lang, etc. The attached data explicitly repeats these patterns with identical answers. 

One particularly important problem

Your state values are:

WCAG pattern 1
WCAG pattern 2
...
WCAG pattern 200

but _meta.pattern only identifies 20 actual concepts.

So the apparent 200-example dataset is somewhat misleading. state is changing, but the actual HTML/question/answer combinations are heavily duplicated.

What I would do before trusting the trained model

I would not retrain yet.

First, fix the dataset generation so that you have substantially more variation per WCAG concept:

1.1.1
 ├─ <img src="x">
 ├─ <img src="x" class="...">
 ├─ decorative image
 ├─ informative image
 ├─ image with incorrect alt
 ├─ SVG
 ├─ linked image
 └─ ...

and similarly for:

1.3.1
3.1.1
1.4.3
2.4.4
2.4.7
4.1.2
...

Then split into train/test by underlying pattern, rather than randomly splitting the duplicated rows. Otherwise the same HTML pattern can occur in both train and test and produce an artificially impressive score.

Bottom line

wcag_train_kev.jsonl is structurally valid and the conversion step worked. 

But the dataset currently looks like a 200-row synthetic repetition of 20 WCAG patterns, not a sufficiently diverse WCAG training corpus.

So the next thing I would verify is the actual Kaggle training output/checkpoint and inference result. If you upload the model output from Kaggle (especially adapter_model.safetensors/checkpoint plus the training log), I can determine whether the 200-row dataset was actually optimized into a Kev adapter and then test whether the resulting model has learned anything beyond memorizing these 20 patterns.
"""
That's fine. We don't need the 35.24 MB adapter_model.safetensors file uploaded here. In fact, the file's existence is already useful evidence that the training pipeline produced a LoRA adapter.

What we need now is to verify what is inside it and whether it is actually the adapter produced by the WCAG training run.

Best way to verify it from Kaggle

Run this in the same Kaggle notebook, after training:

from pathlib import Path
import json
import os

OUT = Path("/kaggle/working/kev-wcag")

print("=== OUTPUT FILES ===")
for p in sorted(OUT.rglob("*")):
    if p.is_file():
        print(f"{p.relative_to(OUT)}  {p.stat().st_size / 1024 / 1024:.2f} MB")

Then inspect the adapter:

from safetensors import safe_open

adapter = OUT / "adapter_model.safetensors"

print("Adapter exists:", adapter.exists())
print("Adapter size:", adapter.stat().st_size / 1024 / 1024, "MB")

with safe_open(adapter, framework="pt") as f:
    keys = list(f.keys())

print("Number of tensors:", len(keys))
print("\nFirst 30 tensors:")
for key in keys[:30]:
    print(key)

The tensor names are particularly important. We should see LoRA/adapter parameters rather than a complete base-model weight dump.

Then verify the adapter configuration

There should normally also be an adapter_config.json. Run:

print("\n=== adapter_config.json ===")

config_file = OUT / "adapter_config.json"

if config_file.exists():
    print(config_file.read_text())
else:
    print("MISSING")

This will tell us things such as:

base model used;

LoRA rank;

target modules;

LoRA alpha;

dropout;

PEFT configuration.


Most important test: reload the trained adapter

This is the test I would trust much more than merely seeing adapter_model.safetensors.

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

BASE = "Qwen/Qwen3-0.6B-Base"
OUT = "/kaggle/working/kev-wcag"

tokenizer = AutoTokenizer.from_pretrained(BASE)

base = AutoModelForCausalLM.from_pretrained(
    BASE,
    dtype=torch.float32,
    device_map="auto",
)

model = PeftModel.from_pretrained(
    base,
    OUT,
)

model.eval()

print("Loaded trained adapter successfully")
print("Trainable parameters:", sum(
    p.numel() for p in model.parameters() if p.requires_grad
))
print("Total parameters:", sum(p.numel() for p in model.parameters()))

Then perform an actual WCAG inference using the reloaded adapter.

For example:

prompt = """Analyze this HTML for WCAG accessibility:

<img src="photo.jpg">

Determine:
1. Does it have a WCAG violation?
2. Which WCAG criterion applies?
3. What is the severity?

Answer concisely.
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    output = model.generate(
        **inputs,
        max_new_tokens=200,
        do_sample=False,
    )

print(tokenizer.decode(output[0], skip_special_tokens=True))

One caveat

I would not use that inference alone as proof that the model learned WCAG.

Given the dataset we inspected, img without alt → 1.1.1 → severity 4 is one of the repeated training patterns. The model could simply have memorized it.

A much more meaningful test would be new HTML that is semantically equivalent but structurally different, for example:

<img class="hero-image" src="/images/product.webp">

or:

<a href="/product">
  <img src="product.jpg">
</a>

Then compare:

Qwen3-0.6B-Base
        vs
Qwen3-0.6B + your trained adapter

on examples not present in the 200 training records.


---

Even easier: you don't need to upload the 35 MB file

If you run the following in Kaggle and paste the output here:

from pathlib import Path
from safetensors import safe_open
import json

OUT = Path("/kaggle/working/kev-wcag")

for name in [
    "adapter_config.json",
    "training_args.bin",
    "trainer_state.json",
]:
    p = OUT / name
    print(f"\n=== {name} ===")
    print("exists:", p.exists())
    if p.exists() and p.suffix == ".json":
        print(p.read_text()[:10000])

adapter = OUT / "adapter_model.safetensors"

print("\n=== adapter ===")
print("exists:", adapter.exists())
print("size:", adapter.stat().st_size if adapter.exists() else None)

if adapter.exists():
    with safe_open(adapter, framework="pt") as f:
        keys = list(f.keys())
        print("tensor count:", len(keys))
        for k in keys[:50]:
            print(k, f.get_tensor(k).shape)

I can then tell you whether the 35.24 MB file is a legitimate trained LoRA adapter, what base model it belongs to, what layers were trained, and whether the Kaggle run appears to have actually produced the intended Kev model.

And if adapter_config.json says Qwen/Qwen3-0.6B-Base, that would also definitively confirm that we've moved past the original Qwen2 import problem.