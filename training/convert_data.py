#!/usr/bin/env python3
"""Convert WCAG training data from old Kev format to current Kev format.

Old format (kev-wcag repo):
  questions: [{
    "type": "noul"|"choice"|"score",
    "instr": "...",
    "options": [...],  # for choice/score
    "label": <bool|int|str>
  }]

Current Kev format (jaredpalmer/kev):
  questions: {
    "has_violation": {
      "type": "noul",
      "instructions": "...",
      "label": true/false
    },
    "which_criterion": {
      "type": "choice",
      "instructions": "...",
      "criteria": {"option A": null, "option B": null},
      "label": "option A"
    },
    "severity": {
      "type": "score",
      "instructions": "...",
      "criteria": ["0", "1", "2", "3", "4"],
      "label": 3
    }
  }
"""

import argparse
import json
from pathlib import Path


def convert_record(record: dict) -> dict:
    """Convert one record from old format to new Kev format."""
    questions = {}

    for i, q in enumerate(record["questions"]):
        if q["type"] == "noul":
            key = "has_violation" if i == 0 else "is_accessible"
            questions[key] = {
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

    return {
        "state": record["state"],
        "questions": questions,
        "_meta": record.get("_meta", {}),
    }


def convert_file(src: Path, dst: Path) -> int:
    """Convert a JSONL file from old to new format. Returns record count."""
    count = 0
    with src.open(encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            record = json.loads(line)
            converted = convert_record(record)
            fout.write(json.dumps(converted, ensure_ascii=False) + "\n")
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Convert WCAG training data to current Kev format"
    )
    parser.add_argument(
        "--src", type=str, default="data/wcag/wcag_train.jsonl",
        help="Source JSONL file in old format"
    )
    parser.add_argument(
        "--dst", type=str, default="data/wcag/wcag_train_kev.jsonl",
        help="Destination JSONL file in new Kev format"
    )
    args = parser.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)

    if not src.exists():
        print(f"Error: source file not found: {src}")
        return 1

    count = convert_file(src, dst)
    print(f"Converted {count} records: {src} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
