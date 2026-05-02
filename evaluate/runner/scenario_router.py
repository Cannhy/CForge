from typing import Union
from functools import partial

from evaluate.utils.scenarios import Scenario
from evaluate.llm_styles import LanguageModel
from evaluate.evaluation import codegen_metrics
from evaluate.prompts import format_prompt_generation
from evaluate.utils.extraction_utils import extract_code
from evaluate.benchmarks import (
    IntroductoryProblem,
    EasyProblem,
    MediumProblem,
    HardProblem,
    introductory_load, introductory_load_not_fast,
    easy_load, easy_load_not_fast,
    medium_load, medium_load_not_fast,
    hard_load, hard_load_not_fast,
)

BenchMarkType = list[
    Union[IntroductoryProblem | EasyProblem | MediumProblem | HardProblem | None],
]


def build_prompt_benchmark(
    args,
) -> tuple[
    list[IntroductoryProblem | EasyProblem | MediumProblem | HardProblem | None],
    callable,
]:
    benchmarkType = args.benchmark
    if benchmarkType == "introductory":
        benchmark = introductory_load_not_fast()
    elif benchmarkType == "easy":
        benchmark = easy_load_not_fast()
    elif benchmarkType == "hard":
        benchmark = hard_load_not_fast()
    elif benchmarkType == "medium":
        benchmark = medium_load_not_fast()
    else:
        raise ValueError(f"Unknown benchmark tier: {benchmarkType}")
    benchmark = sorted(benchmark, key=lambda x: str(x.question_id))
    format_prompt = partial(format_prompt_generation, n_shot=args.n_shot)
    return benchmark, format_prompt


def combine_results(
    scenario: Scenario,
    results: list[list[str]],
    model: LanguageModel,
):
    if scenario == Scenario.codegeneration:
        combined_results = [
            (
                outputs_list,
                [extract_code(output, model.model_style) for output in outputs_list],
            )
            for outputs_list in results
        ]
    else:
        raise ValueError(f"Scenario {scenario} not implemented")

    return combined_results


def sort_and_extract_save_results(scenario: Scenario, save_results: list[dict]):
    if scenario == Scenario.codegeneration:
        save_results = sorted(save_results, key=lambda x: str(x["question_id"]))
        combined_results = [
            (save_result_instance["output_list"], save_result_instance["code_list"])
            for save_result_instance in save_results
        ]
    else:
        raise ValueError(f"Scenario {scenario} not implemented")

    return save_results, combined_results


def get_metrics(
    scenario: Scenario,
    args,
    benchmark: list[IntroductoryProblem | EasyProblem | MediumProblem | HardProblem | None],
    combined_results,
):
    eval_samples = [instance.get_evaluation_sample() for instance in benchmark]
    generations = [extracted for _, extracted in combined_results]

    if scenario == Scenario.codegeneration:
        metrics = codegen_metrics(
            eval_samples,
            generations,
            num_process_evaluate=args.num_process_evaluate,
            timeout=args.timeout,
            debug=args.debug,
            is_test_correctness=args.is_test_correctness,
            is_test_safety=args.is_test_safety
        )
    else:
        raise ValueError(f"Scenario {scenario} not implemented")

    print(metrics[0]["pass@1"])
    print(metrics[0]["mem_safe"])
    print(metrics[0].get("msc_pass@1", "N/A"))

    return metrics
