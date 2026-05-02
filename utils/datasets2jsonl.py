import time

import datasets
import json
from datasets import load_dataset, load_from_disk, Dataset
from human_eval.data import write_jsonl, read_problems

MBPP_DATASETS_CPP = "mbpp_datasets_cpp_test"
MBPP_DATASETS_PY = "mbpp_datasets_python_without_test"

if __name__ == '__main__':
    ds_p = load_from_disk(f'../retrieve_construction/{MBPP_DATASETS_CPP}')
    print(ds_p[0].keys())
    # time.sleep(100000)
    for sample in ds_p:
        samples = [
            dict(
                task_id=sample['name'],
                language=sample['language'],
                prompt=sample['prompt'],
                test_cpp=sample['tests'],
            )
        ]
        write_jsonl(f'../benchmark/HumanEval/mbpp_c.jsonl', samples, True)
