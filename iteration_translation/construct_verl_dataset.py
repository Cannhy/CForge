import os
import re
import json
import gzip
import pandas as pd

from typing import Iterable, Dict
from datasets import Dataset

# from verl.utils.hdfs_io import copy, makedirs
import argparse

def extract_solution(solution_str):
    solution = re.search("#### (\\-?[0-9\\.\\,]+)", solution_str) # extract the solution after ####
    assert solution is not None
    final_solution = solution.group(0)
    final_solution = final_solution.split('#### ')[1].replace(',', '')
    return final_solution

instruction_following = "### Format: Read the inputs from stdin solve the problem and write the answer to stdout (do not directly test on the sample inputs). Ensure that when the C program runs, it reads the inputs, runs the algorithm and writes output to STDOUT."

def make_map_fn(split):
    def process_fn(example, idx):
        question = example.pop('question_content')

        question = '### Question:\n' + question + ' \n' + instruction_following
        question += '```C\n# YOUR CODE HERE\n```\n\n### Answer: (use the provided format with backticks)\n'
        input_output = example.pop('input_output')
        data = {
            "data_source": data_source,
            "prompt": [
                {
                    "role": "system",
                    "content": "You are an expert C programmer. You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests.",
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "ability": "code",
            "reward_model": {
                "style": "rule",
                "ground_truth": ""
            },
            "extra_info": {
                'split': split,
                'index': idx,
                'input_output': input_output,
                'question_id': example['question_id'],
            }
        }
        return data
    return process_fn

# === 你已有的 stream_jsonl 和 read_problems ===
def stream_jsonl(filename: str) -> Iterable[Dict]:
    def read_lines(fp):
        for line_num, line in enumerate(fp, 1):
            if any(not x.isspace() for x in line):
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSONDecodeError at line {line_num}:")
                    print(f"--> {line.strip()}")
                    raise e
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, 'rt', encoding='utf-8') as fp:
                yield from read_lines(fp)
    else:
        with open(filename, "r", encoding='utf-8') as fp:
            yield from read_lines(fp)

def read_problems(evalset_file):
    return list(stream_jsonl(evalset_file))


if __name__ == '__main__':
    default_parquet = os.path.join(
        os.path.dirname(__file__), "..",
        "evaluate", "raw_datasets", "apps_train", "train.parquet",
    )
    parquet_path = os.environ.get("APPS_TRAIN_PARQUET", default_parquet)
    df = pd.read_parquet(parquet_path)

    # 查看数据
    print("行数和列数:", df.shape)
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--local_dir', default='./gsm8k')
    # parser.add_argument('--hdfs_dir', default=None)
    # parser.add_argument('--train_file', required=False)
    # parser.add_argument('--test_file', required=False)
    # local_dir = "./apps_train"
    # hdfs_dir = ""
    # train_file = "./apps_train/apps_train_io.jsonl"
    # args = parser.parse_args()
    #
    # data_source = 'benchC/apps'
    #
    # # 读取 JSONL 并转换成 HuggingFace Dataset 对象
    # train_raw = read_problems(train_file)
    # test_raw = train_raw[0:1]
    #
    # train_dataset = Dataset.from_list(train_raw)
    # test_dataset = Dataset.from_list(test_raw)
    #
    # # 数据预处理
    # train_dataset = train_dataset.map(function=make_map_fn('train'), with_indices=True)
    # test_dataset = test_dataset.map(function=make_map_fn('test'), with_indices=True)
    #
    # # 保存到本地
    # # local_dir = args.local_dir
    # os.makedirs(local_dir, exist_ok=True)
    # train_dataset.to_parquet(os.path.join(local_dir, 'train.parquet'))
    # test_dataset.to_parquet(os.path.join(local_dir, 'test.parquet'))
    #
    # # 拷贝到 hdfs 目录
    # if args.hdfs_dir:
    #     from shutil import copytree
    #     os.makedirs(args.hdfs_dir, exist_ok=True)
    #     copytree(local_dir, args.hdfs_dir, dirs_exist_ok=True)