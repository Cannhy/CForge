import os
import sys
import shutil
import subprocess

sys.set_int_max_str_digits(50000)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json
import multiprocessing
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

_spawn_ctx = multiprocessing.get_context("spawn")


import numpy as np
from tqdm import tqdm

from evaluate.benchmarks.constant import *
from evaluate.evaluation.testing_util import run_test, run_valgrind
from evaluate.evaluation.metric_utils import compute_metrics_from_results, compute_metrics


def check_valgrind_installed():
    """检查 valgrind 是否已安装，未安装则抛出明确错误"""
    if shutil.which("valgrind") is None:
        raise RuntimeError(
            "valgrind is not installed or not found in PATH. "
            "Please install it first:\n"
            "  Ubuntu/Debian: sudo apt-get install valgrind\n"
            "  CentOS/RHEL:   sudo yum install valgrind\n"
            "  macOS:         brew install valgrind"
        )
    try:
        result = subprocess.run(
            ["valgrind", "--version"],
            capture_output=True, text=True, timeout=10
        )
        print(f"[valgrind] Found: {result.stdout.strip()}")
    except Exception as e:
        raise RuntimeError(f"valgrind found but failed to run: {e}")


def _temp_run(sample, generation, debug, result, metadata_list, timeout):
    res, metadata = run_test(sample, gen_code=generation, debug=debug, timeout=timeout)
    result.append(res)
    metadata_list.append(metadata)

def _temp_run_safe(sample, generation, debug, result, metadata_list, timeout):
    res, metadata = run_valgrind(sample, gen_code=generation, debug=debug, timeout=timeout)
    result.append(res)
    metadata_list.append(metadata)

def check_correctness(sample, generation, timeout, debug=True):
    """Check correctness of code generation with a global timeout.
    The global timeout is to catch some extreme/rare cases not handled by the timeouts
    inside `run_test`"""

    manager = multiprocessing.Manager()
    result = manager.list()
    metadata_list = manager.list()
    p = multiprocessing.Process(
        target=_temp_run,
        args=(sample, generation, debug, result, metadata_list, timeout),
    )
    p.start()
    if sample['type'] == ProblemType.IO_BASED or sample['type'] == ProblemType.CALL_BASED_CTYPES:
        timeout = (timeout + 10) * len(json.loads(sample["input_output"])["inputs"]) + 5
        # print(timeout)
        # print("-------")
    else :
        timeout = timeout + 50
    p.join(
        timeout=timeout,
    )
    if p.is_alive():
        p.kill()
    if not result:
        in_outs = json.loads(sample["input_output"])
        # consider that all tests failed
        result = [[-1 for i in range(len(in_outs["inputs"]))]]
        if debug:
            print(f"global timeout")
    return result[0], metadata_list[0]

def check_safety(sample, generation, timeout, debug=True):
    manager = _spawn_ctx.Manager()
    result = manager.list()
    metadata_list = manager.list()
    p = _spawn_ctx.Process(
        target=_temp_run_safe,
        args=(sample, generation, debug, result, metadata_list, timeout),
    )
    p.start()
    if sample['type'] == ProblemType.IO_BASED or sample['type'] == ProblemType.CALL_BASED_CTYPES:
        timeout = (timeout + 10) * len(json.loads(sample["input_output"])["inputs"]) + 5
    else :
        timeout = timeout + 50
    p.join(
        timeout=timeout,
    )
    if p.is_alive():
        p.kill()
    if not result:
        in_outs = json.loads(sample["input_output"])
        # consider that all tests failed
        result = [{}]
        if debug:
            print(f"global timeout")
    return result[0], metadata_list[0]


def evaluate_generations_by_problem(args):
    problem_generations: list[str] = args[0]
    sample = args[1]
    debug: bool = args[2]
    timeout: int = args[3]
    is_test_correctness: bool = args[4]
    is_test_safety: bool = args[5]

    correct_res = []
    metadata = []
    safe_res = []
    safe_metadata = []

    # 计算实际 join timeout
    if sample['type'] == ProblemType.IO_BASED or sample['type'] == ProblemType.CALL_BASED_CTYPES:
        join_timeout = (timeout + 10) * len(json.loads(sample["input_output"])["inputs"]) + 5
    else:
        join_timeout = timeout + 50

    for o_idx, o in enumerate(problem_generations):
        curr_res = [-2]
        curr_metadata = {}
        curr_res_safe = {}
        curr_safe_metadata = {}

        if is_test_correctness and is_test_safety:
            # ---- 并发：同时启动正确性和安全性两个进程 ----
            manager = _spawn_ctx.Manager()

            corr_result = manager.list()
            corr_metadata = manager.list()
            p_corr = _spawn_ctx.Process(
                target=_temp_run,
                args=(sample, o, debug, corr_result, corr_metadata, timeout),
            )

            safe_result = manager.list()
            safe_meta = manager.list()
            p_safe = _spawn_ctx.Process(
                target=_temp_run_safe,
                args=(sample, o, debug, safe_result, safe_meta, timeout),
            )

            # 同时启动
            p_corr.start()
            p_safe.start()

            # 等待两个都完成
            p_corr.join(timeout=join_timeout)
            p_safe.join(timeout=join_timeout)

            if p_corr.is_alive():
                p_corr.kill()
            if p_safe.is_alive():
                p_safe.kill()

            # 正确性结果
            if corr_result:
                curr_res = corr_result[0]
                fixed = []
                for e in curr_res:
                    if isinstance(e, np.ndarray):
                        e = e.item(0)
                    if isinstance(e, np.bool_):
                        e = bool(e)
                    fixed.append(e)
                curr_res = fixed
            else:
                try:
                    in_outs = json.loads(sample["input_output"])
                    curr_res = [-1 for _ in range(len(in_outs["inputs"]))]
                except:
                    curr_res = [-1]
            curr_metadata = corr_metadata[0] if corr_metadata else {"error_code": -3, "error_message": "global timeout"}

            # 安全性结果
            curr_res_safe = safe_result[0] if safe_result else {"memory_leak": 0, "invalid_read": 0, "invalid_write": 0, "use_after_free": 0}
            curr_safe_metadata = safe_meta[0] if safe_meta else {}

            correct_res.append(curr_res)
            metadata.append(curr_metadata)
            safe_res.append(curr_res_safe)
            safe_metadata.append(curr_safe_metadata)

        else:
            # ---- 只跑正确性 ----
            if is_test_correctness:
                try:
                    curr_res, curr_metadata = check_correctness(
                        sample, o, timeout=timeout, debug=debug
                    )
                    fixed = []
                    for e in curr_res:
                        if isinstance(e, np.ndarray):
                            e = e.item(0)
                        if isinstance(e, np.bool_):
                            e = bool(e)
                        fixed.append(e)
                    curr_res = fixed
                except Exception as e:
                    print(f"check_correctness failed, exception = {repr(e)}\n")
                    curr_metadata = {"error": repr(e), "error_code": -5, "error_message": "TestRunnerError"}
                finally:
                    correct_res.append(curr_res)
                    metadata.append(curr_metadata)

            # ---- 只跑安全性 ----
            if is_test_safety:
                try:
                    curr_res_safe, curr_safe_metadata = check_safety(
                        sample, o, timeout=timeout, debug=debug
                    )
                except Exception as e:
                    print(f"check_safety failed, exception = {repr(e)}\n")
                    curr_safe_metadata = {"error": repr(e), "error_code": -5, "error_message": "TestRunnerError"}
                finally:
                    safe_res.append(curr_res_safe)
                    safe_metadata.append(curr_safe_metadata)

    if debug:
        for i, r in enumerate(problem_generations):
            print("Sample\n")
            print(r)
            print("\n")
            print("Result\n")
            print(correct_res[i])
            print("*" * 30 + "\n\n")
    return correct_res, metadata, safe_res, safe_metadata


def evaluate_generations(
    samples_list: list,
    generations_list: list[list[str]],
    debug: bool = False,
    num_process_evaluate: int = 16,
    timeout=6,
    is_test_correctness=True,
    is_test_safety=True
):
    """We take the list of code generations and try to compile them
     and the run their corresponding unit tests which are retrieved from the APPS dataset.

    Args:
        generations: list of code generations (same order as samples in APPS dataset)
        level: difficulty level used in the generation, can be "all", "introductory", "interview" or "competition"

    Returns:
        results: dictionary of results, key is the problem index, value is a list of results for each generation
    """

    # generations are code generations in the same order of the dataset

    inputs = [
        [(generations_list[index], samples_list[index], debug, timeout, is_test_correctness, is_test_safety), index]
        for index in range(len(generations_list))
    ]

    with tqdm(total=len(inputs)) as pbar:
        if debug:
            results = {}
            metadata = {}
            for arg, index in inputs:
                results[index], metadata[index] = evaluate_generations_by_problem(arg)
                pbar.update(1)
        else:
            # 生产模式：多进程加速
            with ProcessPoolExecutor(max_workers=num_process_evaluate) as executor:
                futures = {
                    executor.submit(evaluate_generations_by_problem, arg): index
                    for arg, index in inputs
                }
                results = {}
                metadata = {}
                results_safe = {}
                metadata_safe = {}
                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        results[index], metadata[index], results_safe[index], metadata_safe[index] = future.result()
                    except Exception as e:
                        print(f"[evaluate] Worker crashed for task {index}: {repr(e)}")
                        results[index] = [[-1]]
                        metadata[index] = [{"error": repr(e), "error_code": -6, "error_message": "WorkerCrash"}]
                        results_safe[index] = [{}]
                        metadata_safe[index] = [{"error": repr(e)}]
                    pbar.update(1)

    return results, metadata, results_safe, metadata_safe

    assert len(results) == len(
        inputs
    ), f"results = {len(results)} inputs = {len(inputs)} {results=}"
    # results = {i: r for r, (_, i) in zip(results, inputs)}

    return results, metadata


def codegen_metrics(
    samples_list,
    generations_list,
    k_list=[1, 5, 10, 20, 40, 50, 75, 100, 125, 150, 200, 500, 1000],
    num_process_evaluate=16,
    timeout=6,
    debug=False,
    is_test_correctness=True,
    is_test_safety=True,
):
    # 安全评估前检查 valgrind 是否安装
    if is_test_safety:
        check_valgrind_installed()
    samples_linear = []
    generations_linear = []
    remap_index = []
    results = defaultdict(list)
    metadatas = defaultdict(list)
    results_safe = defaultdict(list)
    metadatas_safe = defaultdict(list)
    for idx, (sample, generation_list) in enumerate(
        zip(samples_list, generations_list)
    ):
        assert isinstance(generation_list, list), generations_list[0]
        for generation in generation_list:
            assert isinstance(generation, str), generations_list[0]
            samples_linear.append(sample)
            generations_linear.append([generation])
            remap_index.append(idx)

    print(f"Evaluating {len(samples_linear)}...")

    results_linear, metadatas_linear, results_safe_linear, metadatas_safe_linear = evaluate_generations(
        samples_linear,
        generations_linear,
        debug=debug,
        num_process_evaluate=num_process_evaluate,
        timeout=timeout,
        is_test_correctness=is_test_correctness,
        is_test_safety=is_test_safety
    )

    for idx, sub_results in sorted(results_linear.items(), key=lambda x: x[0]):
        results[remap_index[idx]].append(sub_results[0])

    for idx, sub_results in sorted(results_safe_linear.items(), key=lambda x: x[0]):
        results_safe[remap_index[idx]].append(sub_results[0])

    for idx, sub_metadatas in sorted(metadatas_linear.items(), key=lambda x: x[0]):
        metadatas[remap_index[idx]].append(sub_metadatas[0])

    for idx, sub_metadatas in sorted(metadatas_safe_linear.items(), key=lambda x: x[0]):
        metadatas_safe[remap_index[idx]].append(sub_metadatas[0])

    samples_dict = {idx: sample for idx, sample in enumerate(samples_list)}

    metrics = compute_metrics(samples_dict, results, results_safe, k_list=k_list)

    final_metadata = []
    for key in sorted(list(metadatas.keys())):
        final_metadata.append(metadatas[key])
    for i in range(len(final_metadata)):
        if type(final_metadata[i]) is not list:
            final_metadata[i] = [json.dumps(final_metadata[i])]
        else:
            final_metadata[i] = [json.dumps(x) for x in final_metadata[i]]

        assert len(final_metadata[i]) == len(
            generations_list[0]
        ), f"{len(final_metadata[i])} != {len(generations_list[0])}"

    # 整理安全性结果：按 problem 维度
    final_safe = []
    for key in sorted(list(results_safe.keys())):
        final_safe.append(results_safe[key])

    return [metrics, results, final_metadata, final_safe]


if __name__ == "__main__":
    print()
    # print(
    #     check_correctness(
    #         {
    #             "input_output": json.dumps(
    #                 {
    #                     "inputs": [
    #                         json.dumps([1] * 100000)
    #                         + "\n"
    #                         + json.dumps([100000, -100000] * (100000 // 2))
    #                     ],
    #                     "outputs": [json.dumps([100000, 0] * (100000 // 2))],
    #                     "fn_name": "mostFrequentIDs",
    #                 }
    #             )
    #         },
    #         "class Solution:\n    def mostFrequentIDs(self, nums: List[int], freq: List[int]) -> List[int]:\n        from collections import defaultdict\n        \n        # Count of each ID\n        count = defaultdict(int)\n        # How many IDs exist for a given frequency\n        freq_of_count = defaultdict(int)\n        \n        max_freq = 0\n        ans = []\n        \n        for i in range(len(nums)):\n            x = nums[i]\n            change = freq[i]\n            \n            old_freq = count[x]\n            new_freq = old_freq + change\n            \n            # If there was an old frequency, decrease its usage\n            if old_freq > 0:\n                freq_of_count[old_freq] -= 1\n                if freq_of_count[old_freq] == 0:\n                    del freq_of_count[old_freq]\n            \n            # Update with the new frequency\n            count[x] = new_freq\n            freq_of_count[new_freq] += 1\n            \n            # Update max_freq if needed\n            if new_freq > max_freq:\n                max_freq = new_freq\n            \n            # If the collection at max_freq is empty, reduce max_freq until we find a non-empty bin\n            while max_freq > 0 and max_freq not in freq_of_count:\n                max_freq -= 1\n            \n            # If the collection is empty, max_freq will be 0\n            ans.append(max_freq)\n        \n        return ans",
    #         6,
    #         debug=True,
    #     )
    # )

    # print(
    #     check_correctness(
    #         {
    #             "input_output": json.dumps(
    #                 {
    #                     "inputs": ")))))",
    #                     "outputs": "0",
    #                 },
    #             )
    #         },
    #         "\nMOD = 998244353\n\nS = input().strip()\nn = len(S)\n\nif n % 2 != 0:\n    print(0)\n    exit()\n\n# Initialize DP table\ndp = [[0] * (n + 2) for _ in range(n + 1)]\ndp[0][0] = 1\n\nfor i in range(1, n + 1):\n    c = S[i-1]\n    for b in range(n + 1):\n        if dp[i-1][b] == 0:\n            continue\n        if c == '(':\n            new_b = b + 1\n            if new_b <= n:\n                dp[i][new_b] = (dp[i][new_b] + dp[i-1][b]) % MOD\n        elif c == ')':\n            if b > 0:\n                new_b = b - 1\n                dp[i][new_b] = (dp[i][new_b] + dp[i-1][b]) % MOD\n        else:  # '?'\n            # Replace with '('\n            new_b = b + 1\n            if new_b <= n:\n                dp[i][new_b] = (dp[i][new_b] + dp[i-1][b]) % MOD\n            # Replace with ')'\n            if b > 0:\n                new_b = b - 1\n                dp[i][new_b] = (dp[i][new_b] + dp[i-1][b]) % MOD\n\nprint(dp[n][0] % MOD)\n",
    #         6,
    #         debug=True,
    #     )
    # )
