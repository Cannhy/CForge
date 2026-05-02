"""
Ad-hoc exploration / debugging script used during dataset construction.

This file contains small experiments for loading and inspecting the raw
intermediate jsonl files. All absolute paths have been replaced with
environment-variable-driven placeholders so this file does not leak any
credentials or private paths.
"""

import os

from evaluate.sandbox.process import write_jsonl
from process_human_eval import read_problems

# Path to the LCB jsonl produced by the translation pipeline; override via
# BENCHC_DATA_ROOT to point to your local copy.
DATA_ROOT = os.environ.get(
    "BENCHC_DATA_ROOT",
    os.path.join(os.path.dirname(__file__), "..", "CForge_data", "data"),
)

LCB_JSONL = os.path.join(DATA_ROOT, "medium", "data.jsonl")


if __name__ == "__main__":
    if not os.path.exists(LCB_JSONL):
        raise FileNotFoundError(
            f"{LCB_JSONL} not found. Set BENCHC_DATA_ROOT or place the data there."
        )
    ds = read_problems(LCB_JSONL)
    print(len(ds))
    for x in ds:
        if x.get("config", "") != "":
            print(x)
            break
