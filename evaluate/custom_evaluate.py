import os
import json

from evaluate.parser import get_args
from evaluate.utils.scenarios import Scenario
from evaluate.utils.path_utils import get_output_path
from evaluate.evaluation import extract_instance_results
from evaluate.runner.scenario_router import (
    build_prompt_benchmark,
    sort_and_extract_save_results,
    get_metrics,
)


def _write_jsonl(path, data_list):
    with open(path, "w", encoding="utf-8") as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _read_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def main():
    args = get_args()

    benchmark, _ = build_prompt_benchmark(args)
    i = 0
    # for x in benchmark:
    #     if str(x.question_id) == "2636":
    #         break
    #     i = i + 1
    # benchmark = benchmark[i : i+1]
    with open(args.custom_output_file, "r") as f:
        content = f.read().strip()
        if content.startswith("["):
            custom_outputs = json.loads(content)
        else:
            custom_outputs = [json.loads(line) for line in content.splitlines() if line.strip()]
        benchmark_new = []
        custom_outputs_new = []
        custom_outputs_dict = dict()
        benchmark_dict = dict()
        for x in custom_outputs:
            custom_outputs_dict[str(x["question_id"])] = x
        for x in benchmark:
            benchmark_dict[str(x.question_id)] = x
        for x in benchmark:
            if str(x.question_id) in custom_outputs_dict:
                benchmark_new.append(x)
        benchmark = benchmark_new
        benchmark = sorted(benchmark, key=lambda x: str(x.question_id))
        for x in custom_outputs:
            if str(x["question_id"]) in benchmark_dict:
                custom_outputs_new.append(x)
        custom_outputs = custom_outputs_new
        assert isinstance(custom_outputs, list)
        assert len(custom_outputs) == len(benchmark), f"{len(custom_outputs)} != {len(benchmark)}"

        is_dict_output = isinstance(custom_outputs[0], dict)

        if is_dict_output:
            assert all(isinstance(custom_output, dict) for custom_output in custom_outputs)
            benchmark = sorted(benchmark, key=lambda x: str(x.question_id))
            custom_outputs = sorted(custom_outputs, key=lambda x: str(x["question_id"]))

            benchmark_dict = {str(instance.question_id): instance for instance in benchmark}
            custom_outputs_dict = {str(entry["question_id"]): entry["code_list"] for entry in custom_outputs}

            assert set(benchmark_dict.keys()) == set(custom_outputs_dict.keys()), \
                f"Mismatch in question_id sets: benchmark({len(benchmark_dict)}) vs outputs({len(custom_outputs_dict)})"

            save_results = []
            for qid in sorted(benchmark_dict.keys()):
                instance = benchmark_dict[qid]
                output_code_list = custom_outputs_dict[qid]
                assert str(instance.question_id) == qid
                save_results.append(instance.insert_output(output_code_list, output_code_list))

        else:
            assert all(isinstance(custom_output, list) for custom_output in custom_outputs)
            save_results = [
                instance.insert_output(custom_output, custom_output)
                for instance, custom_output in zip(benchmark, custom_outputs)
            ]

    save_results, combined_results = sort_and_extract_save_results(args.scenario, save_results)
    benchmark = sorted(benchmark, key=lambda x: str(x.question_id))

    print("start evaluation")
    metrics = get_metrics(args.scenario, args, benchmark, combined_results)
    graded = extract_instance_results(metrics[1])

    if args.scenario == Scenario.codegeneration:
        metadatas = metrics[2]
        safe_results = metrics[3] if len(metrics) > 3 else [[] for _ in benchmark]
        if is_dict_output:
            save_eval_results = []
            for idx, instance in enumerate(benchmark):
                outputs_list, extracted_list = combined_results[idx]
                graded_list = graded[idx]
                meta = metadatas[idx]
                safe = safe_results[idx] if idx < len(safe_results) else []
                save_eval_results.append(
                    instance.insert_output_evaluation(
                        outputs_list, extracted_list, graded_list,
                        metadata=meta, safe_results=safe
                    )
                )
        else:
            save_eval_results = [
                instance.insert_output_evaluation(
                    outputs_list, extracted_list, graded_list,
                    metadata=meta, safe_results=safe
                )
                for instance, (outputs_list, extracted_list), graded_list, meta, safe in zip(
                    benchmark, combined_results, graded, metadatas, safe_results
                )
            ]

    if args.custom_output_save_name is None:
        base = args.custom_output_file
        if base.endswith(".json"):
            base = base[:-5]
            output_path = base + ".jsonl"
        elif base.endswith(".jsonl"):
            # 输入本身就是 jsonl，直接用它作为 output_path（不覆盖，因为内容一样）
            output_path = base
        else:
            output_path = base + ".jsonl"
    else:
        output_path = get_output_path(args.custom_output_save_name, args)

    # 仅当输出路径与输入不同时才写（避免覆盖输入文件）
    if os.path.abspath(output_path) != os.path.abspath(args.custom_output_file):
        _write_jsonl(output_path, save_results)

    eval_path = output_path.replace(".jsonl", "_eval.jsonl")
    with open(eval_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    eval_all_path = output_path.replace(".jsonl", "_eval_all.jsonl")
    _write_jsonl(eval_all_path, save_eval_results)


if __name__ == "__main__":
    main()
