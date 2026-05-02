"""
数据集统计脚本

统计 CForge 四个难度子集（Introductory / Easy / Medium / Hard）的：
1. 样本数量
2. 测试用例数量（总数、平均、min/max/median）
3. 题目类型分布（io_based / call_based / call_based_ctypes）
4. 难度分布（如有）
5. 题目内容长度统计（problem 字符数、参考答案长度）
6. 整体汇总表格
"""

import json
import os
import re
import statistics
from pathlib import Path
from collections import Counter, defaultdict

DATA_ROOT = Path(__file__).resolve().parent.parent / "benchC_data" / "data"

DATASETS = {
    "CForge-Introductory": "introductory/data.jsonl",
    "CForge-Easy":         "easy/data.jsonl",
    "CForge-Medium":       "medium/data.jsonl",
    "CForge-Hard":         "hard/data.jsonl",
}


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def count_test_cases(item):
    """根据题目类型统计测试用例数量"""
    t = item.get("type", "")
    if t in ("io_based", "io", "call_based_ctypes"):
        try:
            io = item["input_output"]
            if isinstance(io, str):
                io = json.loads(io)
            # LCB 的 input_output 是 list，第一个元素可能是 dict 或 string
            if isinstance(io, list) and io:
                io = io[0]
                if isinstance(io, str):
                    io = json.loads(io)
            if isinstance(io, dict):
                return len(io.get("inputs", []))
            return 0
        except Exception:
            return 0
    elif t in ("call_based",):
        # 用 test_code 中 assert 数量近似
        tc = item.get("test_code", "") or ""
        return len(re.findall(r"\bassert\s*\(", tc))
    return 0


def stats_summary(values):
    """计算 min/max/mean/median/total"""
    if not values:
        return {"total": 0, "mean": 0, "min": 0, "max": 0, "median": 0}
    return {
        "total": sum(values),
        "mean": round(statistics.mean(values), 2),
        "min": min(values),
        "max": max(values),
        "median": int(statistics.median(values)),
    }


def analyze_dataset(name, file_path):
    """分析单个数据集"""
    items = list(read_jsonl(file_path))
    n = len(items)

    # 类型分布
    type_counter = Counter(item.get("type", "unknown") for item in items)

    # 难度分布（仅 APPS / LCB 有）
    difficulty_counter = Counter(item.get("difficulty", None) for item in items if item.get("difficulty"))

    # 测试用例数量
    test_counts = [count_test_cases(item) for item in items]

    # 题目长度（字符数）
    question_lens = [len(item.get("question_content", "") or "") for item in items]

    # 参考答案长度（字符数）
    solution_lens = [len(item.get("solution", "") or "") for item in items]

    return {
        "name": name,
        "n_samples": n,
        "type_distribution": dict(type_counter),
        "difficulty_distribution": dict(difficulty_counter) if difficulty_counter else None,
        "test_cases": stats_summary(test_counts),
        "question_chars": stats_summary(question_lens),
        "solution_chars": stats_summary(solution_lens),
    }


def print_dataset_report(report):
    print(f"\n{'='*70}")
    print(f"📊  {report['name']}")
    print(f"{'='*70}")
    print(f"样本数量             : {report['n_samples']}")

    print(f"\n题型分布:")
    for t, c in report['type_distribution'].items():
        print(f"  {t:30s}: {c}")

    if report['difficulty_distribution']:
        print(f"\n难度分布:")
        for d, c in report['difficulty_distribution'].items():
            print(f"  {d:30s}: {c}")

    tc = report['test_cases']
    print(f"\n测试用例数量统计:")
    print(f"  总数  : {tc['total']}")
    print(f"  平均  : {tc['mean']}")
    print(f"  中位数: {tc['median']}")
    print(f"  范围  : [{tc['min']}, {tc['max']}]")

    qc = report['question_chars']
    print(f"\n问题文本长度（字符数）:")
    print(f"  平均  : {qc['mean']}, 中位数: {qc['median']}, 范围: [{qc['min']}, {qc['max']}]")

    sc = report['solution_chars']
    print(f"\n参考解答长度（字符数）:")
    print(f"  平均  : {sc['mean']}, 中位数: {sc['median']}, 范围: [{sc['min']}, {sc['max']}]")


def print_summary_table(reports):
    """打印总览表格（适合直接放论文）"""
    print(f"\n\n{'#'*70}")
    print("# 📑  汇总表格 (适合论文)")
    print(f"{'#'*70}\n")

    # 主表
    header = f"{'Dataset':<20} {'#Samples':>10} {'#TC(total)':>12} {'#TC(avg)':>10} {'IO':>6} {'Call':>6}"
    print(header)
    print("-" * len(header))

    total_samples = 0
    total_tc = 0
    total_io = 0
    total_call = 0

    for r in reports:
        n = r['n_samples']
        tc = r['test_cases']
        td = r['type_distribution']
        n_io = td.get('io_based', 0)
        n_call = td.get('call_based', 0) + td.get('call_based_ctypes', 0)

        total_samples += n
        total_tc += tc['total']
        total_io += n_io
        total_call += n_call

        print(f"{r['name']:<20} {n:>10} {tc['total']:>12} {tc['mean']:>10} {n_io:>6} {n_call:>6}")

    print("-" * len(header))
    overall_avg = round(total_tc / total_samples, 2) if total_samples else 0
    print(f"{'Overall':<20} {total_samples:>10} {total_tc:>12} {overall_avg:>10} {total_io:>6} {total_call:>6}")


def print_latex_table(reports):
    """生成 LaTeX 表格"""
    print(f"\n\n{'#'*70}")
    print("# 📄  LaTeX 表格")
    print(f"{'#'*70}\n")

    print(r"\begin{table}[t]")
    print(r"\centering")
    print(r"\caption{Statistics of the four CForge difficulty tiers.}")
    print(r"\label{tab:dataset_stats}")
    print(r"\begin{tabular}{lcccccc}")
    print(r"\toprule")
    print(r"Dataset & \#Samples & \#TC (Total) & \#TC (Avg) & IO-based & Call-based & Avg.~Solution \\")
    print(r"\midrule")

    total_samples = 0
    total_tc = 0
    total_io = 0
    total_call = 0
    total_sol_len = 0

    for r in reports:
        n = r['n_samples']
        tc = r['test_cases']
        td = r['type_distribution']
        n_io = td.get('io_based', 0)
        n_call = td.get('call_based', 0) + td.get('call_based_ctypes', 0)
        sol_avg = r['solution_chars']['mean']

        total_samples += n
        total_tc += tc['total']
        total_io += n_io
        total_call += n_call
        total_sol_len += sol_avg * n

        print(f"{r['name']} & {n} & {tc['total']} & {tc['mean']} & {n_io} & {n_call} & {sol_avg} \\\\")

    print(r"\midrule")
    overall_avg = round(total_tc / total_samples, 2) if total_samples else 0
    overall_sol = round(total_sol_len / total_samples, 2) if total_samples else 0
    print(f"\\textbf{{Overall}} & \\textbf{{{total_samples}}} & \\textbf{{{total_tc}}} & \\textbf{{{overall_avg}}} & \\textbf{{{total_io}}} & \\textbf{{{total_call}}} & \\textbf{{{overall_sol}}} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")


def main():
    reports = []
    for name, rel_path in DATASETS.items():
        full_path = DATA_ROOT / rel_path
        if not full_path.exists():
            print(f"⚠️  文件不存在: {full_path}")
            continue
        report = analyze_dataset(name, full_path)
        reports.append(report)
        print_dataset_report(report)

    if reports:
        print_summary_table(reports)
        print_latex_table(reports)

        # 同时保存为 JSON 文件方便后续使用
        out_path = Path(__file__).parent / "dataset_stats.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 详细统计已保存到: {out_path}")


if __name__ == "__main__":
    main()
