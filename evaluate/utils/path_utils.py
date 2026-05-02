import pathlib

from evaluate.llm_styles import LanguageModel, LMStyle
from evaluate.utils.scenarios import *


def ensure_dir(path: str, is_file=True):
    if is_file:
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    else:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    return


def get_cache_path(model_repr:str, args) -> str:
    scenario: Scenario = args.scenario
    n = args.n
    temperature = args.temperature
    path = f"cache/{model_repr}/{scenario}_{n}_{temperature}.json"
    ensure_dir(path)
    return path


def get_output_path(model_repr:str, args) -> str:
    scenario: Scenario = args.scenario
    n = args.n
    temperature = args.temperature
    cot_suffix = ""
    benchmark = args.benchmark
    pattern = "zero_shot" if args.n_shot == 0 else f"{args.n_shot}_shot"
    path = f"output/{model_repr}/{benchmark}_{pattern}/code_generation_{n}_{temperature}{cot_suffix}.jsonl"
    ensure_dir(path)
    return path


def get_eval_all_output_path(model_repr:str, args) -> str:
    scenario: Scenario = args.scenario
    n = args.n
    temperature = args.temperature
    cot_suffix = "_cot" if args.cot_code_execution else ""
    benchmark = args.benchmark
    path = f"output/{model_repr}/{benchmark}/code_generation_{n}_{temperature}{cot_suffix}_eval_all.json"
    return path
