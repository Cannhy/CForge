import json
import os
import gzip

from typing import Iterable, Dict
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from evaluate.benchmarks.constant import *
from datasets import load_dataset

LOCAL_MEDIUM_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "benchC_data", "data", "medium", "data.jsonl",
)


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """Parse each jsonl line and yield it as a dictionary."""
    def read_lines(fp):
        for line_num, line in enumerate(fp, 1):
            if any(not x.isspace() for x in line):
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"\n[JSONDecodeError] line {line_num}: {line.strip()}")
                    raise e
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, "rt", encoding="utf-8") as fp:
                yield from read_lines(fp)
    else:
        with open(filename, "r", encoding="utf-8") as fp:
            yield from read_lines(fp)


def read_problems(evalset_file):
    return [task for task in stream_jsonl(evalset_file)]


# Keep these enums for the per-problem metadata fields. They describe the
# *origin* of an individual question, not the dataset name.
class Platform(Enum):
    LEETCODE = "leetcode"
    CODEFORCES = "codeforces"
    ATCODER = "atcoder"


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestType(Enum):
    STDIN = "stdin"
    FUNCTIONAL = "functional"


@dataclass
class Test:
    input: str
    output: str
    testtype: TestType

    def __post_init__(self):
        self.testtype = TestType(self.testtype)


@dataclass
class MediumProblem:
    question_content: str
    platform: Platform
    question_id: str
    contest_date: datetime
    starter_code: str
    difficulty: Difficulty
    type: ProblemType
    public_test_cases: str
    input_output: str
    solution: str
    config: dict

    def __post_init__(self):
        self.platform = Platform(self.platform)
        self.difficulty = Difficulty(self.difficulty)
        self.type = ProblemType(self.type)
        self.contest_date = datetime.fromisoformat(self.contest_date)
        self.question_content = (
            self.question_content
            + "\n"
            + "Ensure the generated code can process the input below.\n"
            + self.public_test_cases
        )
        self.input_output = self.input_output[0]
        self.question_id = str(self.question_id)

    def insert_output(self, output_list: list[str], code_list: list[str]) -> dict:
        return {
            "question_content": self.question_content,
            "platform": self.platform.value,
            "question_id": self.question_id,
            "contest_date": self.contest_date.isoformat(),
            "starter_code": self.starter_code,
            "difficulty": self.difficulty.value,
            "output_list": output_list,
            "code_list": code_list,
        }

    def insert_output_evaluation(
        self,
        output_list: list[str],
        code_list: list[str],
        graded_list: list[bool],
        **kwargs,
    ) -> dict:
        output = self.insert_output(output_list, code_list)
        output["graded_list"] = graded_list
        output["pass@1"] = graded_list.count(True) / len(graded_list)
        for k, v in kwargs.items():
            output[k] = v
        return output

    def get_evaluation_sample(self):
        return {
            "input_output": self.input_output,
            "config": self.config,
            "type": self.type,
            "starter_code": self.starter_code,
            "question_id": self.question_id,
        }


def _load_local(path):
    return read_problems(path)


def _load_from_hf():
    ds = load_dataset(
        "cannhy/benchC", "medium", split="test",
        token=os.getenv("HF_TOKEN"), trust_remote_code=True,
    )
    return [MediumProblem(**p) for p in ds]


def load_code_generation_dataset(
    release_version="release_v6", start_date=None, end_date=None
) -> list[MediumProblem]:
    try:
        dataset = _load_from_hf()
    except Exception as e:
        print(f"Failed to load from HuggingFace: {e}, falling back to local file.")
        dataset = [MediumProblem(**p) for p in _load_local(LOCAL_MEDIUM_PATH)]
    if start_date is not None:
        p_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        dataset = [e for e in dataset if p_start_date <= e.contest_date]
    if end_date is not None:
        p_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        dataset = [e for e in dataset if e.contest_date <= p_end_date]
    print(f"Loaded {len(dataset)} problems")
    return dataset


def load_code_generation_dataset_not_fast(
    release_version="release_v6",
) -> list[MediumProblem]:
    try:
        dataset = _load_from_hf()
    except Exception as e:
        print(f"Failed to load from HuggingFace: {e}, falling back to local file.")
        dataset = [MediumProblem(**p) for p in _load_local(LOCAL_MEDIUM_PATH)]
    print(f"Loaded {len(dataset)} problems")
    return dataset


if __name__ == "__main__":
    dataset = load_code_generation_dataset_not_fast()
