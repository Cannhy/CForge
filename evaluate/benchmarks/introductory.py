import json
import os

from evaluate.benchmarks.constant import *
from datetime import datetime
from dataclasses import dataclass
from datasets import load_dataset

# Local fallback path for the CForge-Introductory tier.
LOCAL_INTRODUCTORY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "benchC_data", "data", "introductory", "data.jsonl",
)


def _load_local_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


@dataclass
class IntroductoryProblem:
    question_content: str
    question_id: str
    starter_code: str
    test_code: str
    solution: str
    type: ProblemType

    def __post_init__(self):
        self.type = ProblemType(self.type)
        self.gen_n = 10

    def insert_output(self, output_list: list[str], code_list: list[str]) -> dict:
        return {
            "question_content": self.question_content,
            "question_id": self.question_id,
            "starter_code": self.starter_code,
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
            "test_code": self.test_code,
            "type": ProblemType.CALL_BASED,
        }


def _load_from_hf():
    ds = load_dataset(
        "cannhy/benchC", "introductory", split="test",
        token=os.getenv("HF_TOKEN"), trust_remote_code=True,
    )
    return [IntroductoryProblem(**p) for p in ds]


def load_code_generation_dataset(
    release_version="release_v1", start_date=None, end_date=None
) -> list[IntroductoryProblem]:
    try:
        dataset = _load_from_hf()
    except Exception as e:
        print(f"Failed to load from HuggingFace: {e}, falling back to local file.")
        dataset = [IntroductoryProblem(**p) for p in _load_local_jsonl(LOCAL_INTRODUCTORY_PATH)]
    if start_date is not None:
        p_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        dataset = [e for e in dataset if p_start_date <= e.contest_date]
    if end_date is not None:
        p_end_date = datetime.strptime(end_date, "%Y-%m-%d")
        dataset = [e for e in dataset if e.contest_date <= p_end_date]
    print(f"Loaded {len(dataset)} problems")
    return dataset


def load_code_generation_dataset_not_fast(
    release_version="release_v1",
) -> list[IntroductoryProblem]:
    try:
        dataset = _load_from_hf()
    except Exception as e:
        print(f"Failed to load from HuggingFace: {e}, falling back to local file.")
        dataset = [IntroductoryProblem(**p) for p in _load_local_jsonl(LOCAL_INTRODUCTORY_PATH)]
    print(f"Loaded {len(dataset)} problems")
    return dataset


if __name__ == "__main__":
    dataset = load_code_generation_dataset()
