import numpy as np

from evaluate.benchmarks.constant import *


def estimate_pass_at_k(num_samples, num_correct, k):
    """Estimates pass@k of each problem and returns them in an array."""

    def estimator(n: int, c: int, k: int) -> float:
        """Calculates 1 - comb(n - c, k) / comb(n, k)."""
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

    import itertools

    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    return np.array(
        [estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)]
    )


def compute_metrics_from_results(results, k_list=[1, 5]):
    total = []
    correct = []
    task_ids = []
    for task_id, res in results.items():
        all_correct = []
        for generation in res:
            gen = np.array(generation)
            all_correct.append(np.all(gen > 0))
        task_ids.append(task_id)
        total.append(len(all_correct))
        correct.append(sum(all_correct))
    total = np.array(total)
    correct = np.array(correct)
    ks = k_list
    detail_pass_at_k = {
        f"pass@{k}": estimate_pass_at_k(total, correct, k).tolist()
        for k in ks
        if (total >= k).all()
    }
    pass_at_k = {
        f"pass@{k}": estimate_pass_at_k(total, correct, k).mean()
        for k in ks
        if (total >= k).all()
    }
    detail_metrics = {k: dict(zip(task_ids, v)) for k, v in detail_pass_at_k.items()}
    pass_at_k["detail"] = detail_metrics
    return pass_at_k


ERROR_KEYS = ("memory_leak", "invalid_read", "invalid_write", "use_after_free")

def _compute_caps(results_safe, cap_percentile=95):
    """从所有任务/生成里统计每种错误的分位数作为封顶值"""
    all_counts = {k: [] for k in ERROR_KEYS}
    for safe_list in results_safe.values():
        if not isinstance(safe_list, list):
            continue
        for item in safe_list:
            if not isinstance(item, dict):
                continue
            for k in ERROR_KEYS:
                v = item.get(k, 0)
                try:
                    all_counts[k].append(int(v))
                except Exception:
                    pass
    caps = {}
    for k in ERROR_KEYS:
        if all_counts[k]:
            cap = int(np.percentile(all_counts[k], cap_percentile))
            caps[k] = max(cap, 1)  # 至少为 1，避免除零
        else:
            caps[k] = 1
    return caps

def _mem_safe_for_code(err_dict, caps):
    if not isinstance(err_dict, dict):
        return 1.0
    total_errs = sum(max(0, int(err_dict.get(k, 0))) for k in ERROR_KEYS)
    return 1.0 / (1.0 + total_errs)

def compute_metrics(samples, results, results_safe, k_list=[1, 5], cap_percentile=100):
    """
    Args:
        samples: 每个任务的元信息
        results: {task_id: [[test_result, ...], ...]}  每任务多次生成的测试结果
        results_safe: {task_id: [err_dict, ...]}  每任务多次生成的内存安全检测结果
        k_list: pass@k 中的 k 值列表
        cap_percentile: MSC 封顶分位数
    """
    # ------- pass@k 计算 -------
    total = []
    correct = []
    msc_correct = []  # MSC-pass@k: 通过测试 + 完全内存安全
    task_ids = []

    # 先计算归一化封顶值
    caps = _compute_caps(results_safe, cap_percentile=cap_percentile)

    # 每任务 memory safety
    mem_safe_per_task = {}

    for task_id, res in results.items():
        all_correct = []
        safe_list = results_safe.get(task_id, [])
        gen_cnt = len(res)

        # 逐生成的 mem_safe
        mem_safes_this_task = []
        msc_pass_count = 0

        smp = samples[task_id]

        for idx, generation in enumerate(res):
            gen = np.array(generation)
            passed = bool(np.all(gen > 0))
            all_correct.append(passed)

            # 和 results_safe 对齐：若缺项，按无错处理
            err_dict = None
            if isinstance(safe_list, list) and idx < len(safe_list):
                err_dict = safe_list[idx]

            msc_gen = 1.0
            if smp["type"] == ProblemType.IO_BASED or smp["type"] == ProblemType.CALL_BASED:
                msc_gen = _mem_safe_for_code(err_dict, caps)
                mem_safes_this_task.append(msc_gen)

            # MSC-pass@k: 通过测试 且 完全内存安全(MSC==1.0) 才算通过
            if passed and msc_gen == 1.0:
                msc_pass_count += 1

        task_ids.append(task_id)
        total.append(len(all_correct))
        correct.append(sum(all_correct))
        msc_correct.append(msc_pass_count)

        # 任务级 mem_safe：所有生成的最小值
        mem_safe_per_task[task_id] = float(np.min(mem_safes_this_task) if mem_safes_this_task else 1.0)

    total = np.array(total)
    correct = np.array(correct)
    msc_correct = np.array(msc_correct)

    # ------- 汇总指标 -------
    ks = k_list
    detail_pass_at_k = {
        f"pass@{k}": estimate_pass_at_k(total, correct, k).tolist()
        for k in ks if (total >= k).all()
    }
    metrics = {
        f"pass@{k}": float(estimate_pass_at_k(total, correct, k).mean())
        for k in ks if (total >= k).all()
    }

    # MSC-pass@k: 用 msc_correct 替代 correct 计算 pass@k
    for k in ks:
        if (total >= k).all():
            metrics[f"msc_pass@{k}"] = float(estimate_pass_at_k(total, msc_correct, k).mean())

    # 全局 mem_safe：各任务 mem_safe 的平均
    metrics["mem_safe"] = float(np.mean(list(mem_safe_per_task.values()))) if mem_safe_per_task else 1.0
    # metrics["mem_safe_detail"] = mem_safe_per_task  # 可选：保留每任务明细
    # metrics["mem_safe_caps"] = caps                 # 可选：记录用到的封顶值，便于解释

    # pass@k 明细
    detail_metrics = {k: dict(zip(task_ids, v)) for k, v in detail_pass_at_k.items()}
    metrics["pass@k_detail"] = detail_metrics

    return metrics

def extract_instance_results(results):
    instance_wise_grades = {}
    for task_id, res in results.items():
        instance_wise_grades[task_id] = []
        for generation in res:
            instance_wise_grades[task_id].append(all([g > 0 for g in generation]))

    instance_wise_grades = [
        v for _, v in sorted(instance_wise_grades.items(), key=lambda item: item[0])
    ]
    return instance_wise_grades
