import os
import json
import threading

from evaluate.parser import get_args
from evaluate.llm_styles import LanguageModelStore
from evaluate.runner.runner_utils import build_runner
from evaluate.utils.path_utils import get_output_path
from evaluate.evaluation import extract_instance_results
from evaluate.utils.extraction_utils import extract_code
from evaluate.runner.scenario_router import (
    build_prompt_benchmark,
    combine_results,
    sort_and_extract_save_results,
    get_metrics,
)


def _write_jsonl(path, data_list):
    # write-then-rename for crash safety while streaming
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    os.replace(tmp_path, path)


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

    model = LanguageModelStore[args.model]
    benchmark, format_prompt = build_prompt_benchmark(args)
    # benchmark = benchmark[:4995]
    # i = 0
    # for x in benchmark:
    #     if str(x.question_id) == "2726":
    #         print(i)
    #         break
    #     i += 1
    # benchmark = benchmark[i:i + 1]
    if args.debug:
        print(f"Running with {len(benchmark)} instances in debug mode")
        i = 0
        for x in benchmark:
            if str(x.question_id) == "93":
                # print(i)
                break
            i += 1
        benchmark = benchmark[i:i+1]

    # print(benchmark)
    output_path = get_output_path(model.model_repr, args)
    eval_file = output_path.replace(".jsonl", "_eval.jsonl")
    eval_all_file = output_path.replace(".jsonl", "_eval_all.jsonl")
    part_gen_num = dict()
    part_gen_results = dict()
    part_gen_qc = dict()
    part_gen_dec = dict()
    part_gen_codes = dict()
    if args.continue_existing or args.continue_existing_with_eval:
        if os.path.exists(output_path):
            old_save_results = _read_jsonl(output_path)
        elif os.path.exists(eval_all_file):
            old_save_results = _read_jsonl(eval_all_file)
        else:
            print(
                f"File {output_path} does not exist in --continue_existing, starting from scratch"
            )
            old_save_results = []
        for x in old_save_results:
            gen_num = sum(1 for s in x["code_list"] if s.strip() != "")
            if gen_num < args.n:
                target_num = args.n - gen_num
                print(f'question_id: {x["question_id"]} gen_num: {gen_num} target_num: {target_num}')
                part_gen_num[str(x["question_id"])] = target_num
                part_gen_results[str(x["question_id"])] = [x["output_list"][i] for i, output in enumerate(x["code_list"]) if output != ""]
                part_gen_codes[str(x["question_id"])] = [code for code in x["code_list"] if code != ""]
                part_gen_qc[str(x["question_id"])] = x["question_content"]
                part_gen_dec[str(x["question_id"])] = x["starter_code"]
        old_save_results = [
                instance
                for instance in old_save_results
                if instance["code_list"] and all(x != "" for x in instance["code_list"]) and len(instance["code_list"]) == args.n
            ]
        old_save_results_question_ids = [
            str(instance["question_id"]) for instance in old_save_results
        ]
        # print(old_save_results_question_ids)
        remaining_benchmark = [
            instance
            for instance in benchmark
            if str(instance.question_id) not in old_save_results_question_ids
        ]
        # for x in remaining_benchmark:
        #     print(x.question_id)
        print(
            f"Found {len(old_save_results)} existing generations, continuing with {len(remaining_benchmark)} remaining"
        )
    else:
        old_save_results = []
        remaining_benchmark = benchmark
        for x in remaining_benchmark:
            part_gen_num[str(x.question_id)] = args.n

    if len(remaining_benchmark) > 0:
        runner = build_runner(args, model, part_gen_num)

        # 内存中维护最新的 save_results 视图，以 question_id 为键
        # 先把"已经完整"的旧结果放进来
        live_results_dict: dict[str, dict] = {
            str(x["question_id"]): x for x in old_save_results
        }
        # 再把"部分生成过但不完整"的条目放进去（后续每生成 1 个就 append 上去）
        for qid in part_gen_results.keys():
            live_results_dict.setdefault(str(qid), {
                "question_content": part_gen_qc[qid],
                "starter_code": part_gen_dec[qid],
                "question_id": str(qid),
                "output_list": list(part_gen_results[qid]),
                "code_list": list(part_gen_codes[qid]),
            })
        # 为 remaining_benchmark 中此前没任何记录的题预建骨架，便于 on_sample 直接 append
        for problem in remaining_benchmark:
            qid = str(problem.question_id)
            if qid not in live_results_dict:
                live_results_dict[qid] = {
                    "question_content": getattr(problem, "question_content", ""),
                    "starter_code": getattr(problem, "starter_code", ""),
                    "question_id": qid,
                    "output_list": [],
                    "code_list": [],
                }
                # 若 benchmark 有其他字段（platform/difficulty/contest_date），保留
                for extra in ("platform", "difficulty", "contest_date"):
                    v = getattr(problem, extra, None)
                    if v is not None:
                        # enum / datetime 尽力序列化
                        try:
                            live_results_dict[qid][extra] = v.value
                        except AttributeError:
                            try:
                                live_results_dict[qid][extra] = v.isoformat()
                            except AttributeError:
                                live_results_dict[qid][extra] = v

        write_lock = threading.Lock()

        def _flush_snapshot():
            snapshot = sorted(
                live_results_dict.values(),
                key=lambda x: str(x["question_id"]),
            )
            _write_jsonl(output_path, snapshot)

        def _on_one_sample(problem, raw_output: str):
            """每完成一个样本（1 次 API 调用）就回调：抽取 code → append 到该题的 list → flush 落盘。"""
            try:
                code = extract_code(raw_output, model.model_style)
            except Exception as e:
                print(f"[on_sample] extract_code failed for qid={problem.question_id}: {e!r}")
                code = ""
            qid = str(problem.question_id)
            with write_lock:
                entry = live_results_dict.setdefault(qid, {
                    "question_content": getattr(problem, "question_content", ""),
                    "starter_code": getattr(problem, "starter_code", ""),
                    "question_id": qid,
                    "output_list": [],
                    "code_list": [],
                })
                entry["output_list"].append(raw_output)
                entry["code_list"].append(code)
                try:
                    _flush_snapshot()
                except Exception as e:
                    print(f"[on_sample] flush jsonl failed: {e!r}")

        runner.run_main_per_sample(
            benchmark=remaining_benchmark,
            format_prompt=format_prompt,
            on_sample=_on_one_sample,
        )
        results = []  # not used downstream; combined_results rebuilt from live_results_dict
    else:
        results = []
        live_results_dict = {str(x["question_id"]): x for x in old_save_results}
        # 纯续跑路径下仍然可能有 part_gen（虽然此时 remaining_benchmark==0，极少见）
        for qid in part_gen_results.keys():
            if str(qid) not in live_results_dict:
                live_results_dict[str(qid)] = {
                    "question_content": part_gen_qc[qid],
                    "starter_code": part_gen_dec[qid],
                    "question_id": str(qid),
                    "output_list": list(part_gen_results[qid]),
                    "code_list": list(part_gen_codes[qid]),
                }

    # 流式落盘已经把所有 new_results + old + part_gen 合并到 live_results_dict 中，
    # 这里直接从它取最终 save_results（并排序），无需再额外拼装。
    save_results = sorted(
        live_results_dict.values(), key=lambda x: str(x["question_id"])
    )

    # 供后续评估使用的按 benchmark 顺序对齐的 combined_results。
    # evaluate 分支下面用 benchmark 的顺序做索引，所以这里按 question_id 取。
    _sr_by_qid = {str(x["question_id"]): x for x in save_results}
    combined_results = [
        (
            _sr_by_qid[str(b.question_id)]["output_list"],
            _sr_by_qid[str(b.question_id)]["code_list"],
        )
        if str(b.question_id) in _sr_by_qid
        else ([], [])
        for b in benchmark
    ]

    # 兜底再写一次（流式写过，但如果 remaining==0 分支未触发流式写，这里仍保证文件存在）
    _write_jsonl(output_path, list(save_results))

    if args.evaluate:
        if args.continue_existing_with_eval and os.path.exists(eval_all_file):
            old_eval_all_results = _read_jsonl(eval_all_file)

            if os.path.exists(eval_file):
                _old_eval_lines = _read_jsonl(eval_file)
                # eval_file 写入的是一整行 metrics list: [metrics_dict, results_dict, ...]
                old_eval_results = _old_eval_lines[0] if _old_eval_lines else None
            else:
                old_eval_results = None

            old_eval_results_question_ids = [
                instance["question_id"] for instance in old_eval_all_results
            ]
            remaining_indices = [
                idx
                for idx in range(len(benchmark))
                if benchmark[idx].question_id not in old_eval_results_question_ids
            ]
            benchmark = [benchmark[idx] for idx in remaining_indices]
            combined_results = [combined_results[idx] for idx in remaining_indices]

            old_eval_size = len(old_eval_results_question_ids)
            new_eval_size = len(benchmark)

            if new_eval_size == 0:
                return

            print(f"Found {old_eval_size}, running evals for {new_eval_size} problems")

            metrics = get_metrics(args.scenario, args, benchmark, combined_results)
            graded = extract_instance_results(metrics[1])

            if old_eval_results:
                import math
                for key in list(metrics[0].keys()):
                    if key in old_eval_results[0]:
                        # 只对数值类型做加权平均，跳过 dict/list/str 类型
                        if isinstance(metrics[0][key], (int, float)) and isinstance(old_eval_results[0][key], (int, float)):
                            old_v = old_eval_results[0][key]
                            new_v = metrics[0][key]
                            # 如果旧值或新值是 NaN，则取另一个有效值，避免 NaN 污染
                            if isinstance(old_v, float) and math.isnan(old_v):
                                continue  # 保留 new_v
                            if isinstance(new_v, float) and math.isnan(new_v):
                                metrics[0][key] = old_v
                                continue
                            metrics[0][key] = (
                                old_eval_size * old_v + new_eval_size * new_v
                            ) / (old_eval_size + new_eval_size)

                # 合并 pass@k_detail
                for key in metrics[0].get("pass@k_detail", {}):
                    if key in old_eval_results[0].get("pass@k_detail", {}):
                        metrics[0]["pass@k_detail"][key] = {
                            **metrics[0]["pass@k_detail"][key],
                            **old_eval_results[0]["pass@k_detail"][key],
                        }
                metrics[1] = {**metrics[1], **old_eval_results[1]}
            else:
                print("Old eval file not present, cannot update eval file")
                metrics = {}

        else:
            metrics = get_metrics(args.scenario, args, benchmark, combined_results)
            graded = extract_instance_results(metrics[1])
            old_eval_all_results = []
            old_eval_results = []

        if metrics:
            metadatas = metrics[2]
            safe_results = metrics[3] if len(metrics) > 3 else [[] for _ in benchmark]
        else:
            metadatas = [[] for _ in benchmark]
            safe_results = [[] for _ in benchmark]
        save_eval_results = [
            instance.insert_output_evaluation(
                outputs_list, extracted_list, graded_list,
                metadata=meta, safe_results=safe
            )
            for instance, (outputs_list, extracted_list), graded_list, meta, safe in zip(
                benchmark, combined_results, graded, metadatas, safe_results
            )
        ]
        if metrics and old_eval_results:
            # 合并旧的 metadata 和 safe_results
            if len(old_eval_results) > 2 and len(metrics) > 2:
                metrics[2] = old_eval_results[2] + metrics[2]
            if len(old_eval_results) > 3 and len(metrics) > 3:
                metrics[3] = old_eval_results[3] + metrics[3]

        save_eval_results = old_eval_all_results + save_eval_results

        with open(eval_file, "w") as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + "\n")

        _write_jsonl(eval_all_file, save_eval_results)


if __name__ == "__main__":
    main()
