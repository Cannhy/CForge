import os
import json
import time
import subprocess
import tempfile
import numpy as np
import pytz
import re

from decimal import Decimal
from decimal import InvalidOperation
import logging
import os
from datetime import datetime

timezone = pytz.timezone('Asia/Shanghai')
timestamp = datetime.now(timezone).strftime("%Y%m%d_%H%M%S")
log_dir = "log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, f"training_{timestamp}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

def extract_code(model_output: str):
    outputlines = model_output.split("\n")
    indexlines = [i for i, line in enumerate(outputlines) if "```" in line]
    if len(indexlines) < 2:
        return ""
    return "\n".join(outputlines[indexlines[-2] + 1 : indexlines[-1]])

def convert_line_to_decimals(line: str):
    try:
        return True, [Decimal(token) for token in line.split()]
    except InvalidOperation:
        return False, []

def get_stripped_lines(val: str):
    ## you don't want empty lines to add empty list after splitlines!
    val = val.strip()

    return [val_line.strip() for val_line in val.split("\n")]

def normalize_input(gt_inp):
    if isinstance(gt_inp, str):
        return gt_inp
    elif isinstance(gt_inp, list):
        # 处理三维及二维列表结构
        lines = []
        for item in gt_inp:
            if isinstance(item, list):
                for subitem in item:
                    if isinstance(subitem, list):
                        # 三维结构 -> 把 [2,9,10] 转成 '2 9 10'
                        lines.append(" ".join(map(str, subitem)))
                    else:
                        # 二维结构 -> 把 [2,9,10] 转成 '2 9 10'
                        lines.append(" ".join(map(str, item)))
                        break  # 防止重复添加
            else:
                # 一维结构
                lines.append(str(item))
        return "\n".join(lines)
    else:
        return str(gt_inp)

def truncatefn(s, length=300):
    if isinstance(s, str):
        pass
    else:
        s = str(s)
    if len(s) <= length:
        return s

    return s[: length // 2] + "...(truncated) ..." + s[-length // 2 :]

def disable_core():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def get_valgrind_errors(code: str, all_inputs: list[str], timeout: int):
    max_error_counts = {
        "memory_leak": 0,
        "invalid_read": 0,
        "invalid_write": 0,
        "use_after_free": 0
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "main.c")
        binary_path = os.path.join(tmpdir, "main.out")

        # 写入 C 代码
        with open(source_path, "w") as f:
            f.write(code)

        # 编译 C 程序
        try:
            subprocess.run(
                ["gcc", source_path, "-o", binary_path],  # -g 方便valgrind调试
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=True
            )
        except subprocess.CalledProcessError as e:
            return max_error_counts, {
                "error_code": -1,
                "error_message": "Compile Error",
                "output": e.stderr.decode(),
            }
        except subprocess.TimeoutExpired:
            return max_error_counts, {
                "error_code": -3,
                "error_message": "Compile Timeout",
            }

        max_error_counts = {
            "memory_leak": 0,
            "invalid_read": 0,
            "invalid_write": 0,
            "use_after_free": 0
        }
        all_results = []
        if len(all_inputs) == 0:
            try:
                proc = subprocess.run(
                    [
                        "valgrind",
                        "--leak-check=full",
                        "--track-origins=yes",
                        "--show-leak-kinds=all",
                        "--trace-children=yes",
                        "--error-exitcode=123",  # 检测错误
                        "--log-fd=2",            # 所有 Valgrind 日志都输出到 stderr
                        binary_path,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    preexec_fn=disable_core
                )
            except subprocess.TimeoutExpired:
                return max_error_counts, {
                    "error_code": -3,
                    "error_message": "Time Limit Exceeded",
                }
            except Exception as e:
                return max_error_counts, {
                    "error_code": -4,
                    "error_message": f"Runtime Error: {e}",
                }

            stdout = proc.stdout.decode(errors="ignore")
            stderr = proc.stderr.decode(errors="ignore")

            stderr = stderr.lower()
            mem_leak = len(re.findall(r"definitely lost: (\d+) bytes", stderr))
            invalid_read = len(re.findall(r"invalid read of size \d+", stderr))
            invalid_write = len(re.findall(r"invalid write of size \d+", stderr))
            use_after_free = len(re.findall(r"use of freed memory", stderr))

            max_error_counts["memory_leak"] = max(max_error_counts["memory_leak"], mem_leak)
            max_error_counts["invalid_read"] = max(max_error_counts["invalid_read"], invalid_read)
            max_error_counts["invalid_write"] = max(max_error_counts["invalid_write"], invalid_write)
            max_error_counts["use_after_free"] = max(max_error_counts["use_after_free"], use_after_free)
            return max_error_counts, {}

        for gt_inp in all_inputs:
            input_str = gt_inp  # 这里假设输入不需要额外处理

            # 用valgrind执行程序，捕获valgrind的详细日志
            try:
                proc = subprocess.run(
                    [
                        "valgrind",
                        "--leak-check=full",
                        "--track-origins=yes",
                        "--show-leak-kinds=all",
                        "--trace-children=yes",
                        "--error-exitcode=123",  # 检测错误
                        "--log-fd=2",            # 所有 Valgrind 日志都输出到 stderr
                        binary_path,
                    ],
                    input=input_str.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    preexec_fn=disable_core
                )
            except subprocess.TimeoutExpired:
                return max_error_counts, {
                    "error_code": -3,
                    "error_message": "Time Limit Exceeded",
                    "inputs": gt_inp,
                }
            except Exception as e:
                return max_error_counts, {
                    "error_code": -4,
                    "error_message": f"Runtime Error: {e}",
                    "inputs": gt_inp,
                }

            stdout = proc.stdout.decode(errors="ignore")
            stderr = proc.stderr.decode(errors="ignore")
            # print(f"stderr: {stderr}")

            stderr = stderr.lower()
            mem_leak = len(re.findall(r"definitely lost: (\d+) bytes", stderr))
            invalid_read = len(re.findall(r"invalid read of size \d+", stderr))
            invalid_write = len(re.findall(r"invalid write of size \d+", stderr))
            use_after_free = len(re.findall(r"use of freed memory", stderr))

            max_error_counts["memory_leak"] = max(max_error_counts["memory_leak"], mem_leak)
            max_error_counts["invalid_read"] = max(max_error_counts["invalid_read"], invalid_read)
            max_error_counts["invalid_write"] = max(max_error_counts["invalid_write"], invalid_write)
            max_error_counts["use_after_free"] = max(max_error_counts["use_after_free"], use_after_free)
            # if mem_leak != 0:
            #     print(f"{max_error_counts} {stderr}")
            # all_results.append({
            #     "stdout": stdout,
            #     "valgrind_stderr": stderr,
            #     "errors": {
            #         "memory_leak": mem_leak,
            #         "invalid_read": invalid_read,
            #         "invalid_write": invalid_write,
            #         "use_after_free": use_after_free
            #     }
            # })

        return max_error_counts, {}

def grade_stdio(code: str, all_inputs: list[str], all_outputs: list[str], timeout: int):
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "main.c")
        binary_path = os.path.join(tmpdir, "main.out")

        # 写入 C 代码
        with open(source_path, "w") as f:
            f.write(code)

        # 编译 C 程序
        try:
            compile_proc = subprocess.run(
                ["gcc", source_path, "-o", binary_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return [-1], {
                "error_code": -1,
                "error_message": "Compile Error",
                "output": e.stderr.decode(),
            }
        except subprocess.TimeoutExpired:
            return [-3], {
                "error_code": -3,
                "error_message": "Compile Timeout",
            }

        all_results = []
        total_execution_time = 0

        # 逐个运行测试用例
        for gt_inp, gt_out in zip(all_inputs, all_outputs):
            try:
                start = time.time()
                input_str = normalize_input(gt_inp)
                proc = subprocess.run(
                    [binary_path],
                    input=input_str.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                )
                total_execution_time += time.time() - start
            except subprocess.TimeoutExpired:
                return [-3], {
                    "error_code": -3,
                    "error_message": "Time Limit Exceeded",
                    "inputs": truncatefn(gt_inp),
                    "expected": truncatefn(gt_out),
                }
            except Exception as e:
                print(e)
                return [-4], {
                    "error_code": -4,
                    "error_message": "Runtime Error",
                    "inputs": truncatefn(gt_inp),
                    "expected": truncatefn(gt_out),
                }

            output = proc.stdout.decode(errors="ignore")
            stripped_output = get_stripped_lines(output)
            stripped_expected = get_stripped_lines(normalize_input(gt_out))

            WA_send_args = {
                "output": truncatefn(output),
                "inputs": truncatefn(gt_inp),
                "expected": truncatefn(gt_out),
                "error_code": -2,
            }

            if len(stripped_output) != len(stripped_expected):
                all_results.append(-2)
                WA_send_args["error_message"] = "Wrong answer: mismatched output length"
                return all_results, WA_send_args

            for idx, (pred_line, exp_line) in enumerate(zip(stripped_output, stripped_expected)):
                if pred_line == exp_line:
                    continue

                success1, pred_dec = convert_line_to_decimals(pred_line)
                success2, exp_dec = convert_line_to_decimals(exp_line)

                if not (success1 and success2):
                    all_results.append(-2)
                    WA_send_args["error_message"] = (
                        f"Wrong answer at line {idx}: {truncatefn(pred_line)} != {truncatefn(exp_line)}"
                    )
                    return all_results, WA_send_args

                if pred_dec == exp_dec:
                    continue

                all_results.append(-2)
                WA_send_args["error_message"] = (
                    f"Wrong answer at line {idx}: {truncatefn(pred_line)} != {truncatefn(exp_line)}"
                )
                return all_results, WA_send_args

            all_results.append(True)

    return all_results, {"execution_time": total_execution_time}

def get_execute_result(code, input_output):
    # print(f"type(code): {type(code)}, type(input_output): {type(input_output)}")
    # print(f"code: {code[:50]}, input_output: {input_output[:50]}")
    in_outs = json.loads(input_output)
    try:
        results, metadata = grade_stdio(
            code=code,
            all_inputs=in_outs["inputs"],
            all_outputs=in_outs["outputs"],
            timeout=5,
        )
        return results, metadata
    except Exception as e:
        return [-4], {
            "error_code": -4,
            "error_message": f"Error during testing: {e}",
        }

def compute_score(data_source, solution_str, ground_truth, extra_info=None) -> float:
    input_output = json.dumps(extra_info.get("input_output"))
    solution_str = extract_code(solution_str)
    run_res, run_dict = get_execute_result(solution_str, input_output)
    # logger.info(f"[run_res]:\n {run_res}")
    # logger.info(f"run_dict: {run_dict}")
    is_pass = all(x is True for x in run_res)
    # print(f"is_pass={is_pass}")
    reward = 1.0 if is_pass else 0.0
    safe_error_dic, metadatas = get_valgrind_errors(solution_str, extra_info.get("input_output"), 10)
    # logger.info(f"[valgrind_error_count]:\n {cppcheck_error_count}")
    alpha = 0.1
    # penalty = alpha * cppcheck_error_count
    #
    safe_score_penalty = 0.1 * safe_error_dic["memory_leak"] + 0.05 * safe_error_dic["invalid_read"] + 0.05 * safe_error_dic["invalid_write"] + 0.1 * safe_error_dic["use_after_free"]
    if reward == 1.0:
        if safe_score_penalty == 0:
            reward += 0.2
        else:
            reward -= max(safe_score_penalty, 0.2)
    logger.info(f"[reward]: {reward}")
    return reward

if __name__ == "__main__":
    solution_str = "#include <stdio.h>\n#include <stdlib.h>\n\nvoid read_data() {\n    int *arr = (int *)malloc(10 * sizeof(int));  // 动态分配内存\n    if (arr == NULL) {\n        printf(\"内存分配失败\\n\");\n        return;\n    }\n\n    // 从标准输入读取数据\n    printf(\"请输入10个整数：\\n\");\n    for (int i = 0; i < 10; i++) {\n        scanf(\"%d\", &arr[i]);  // 将输入的整数存储到数组中\n    }\n\n    // 注意：没有释放动态分配的内存，造成内存泄漏\n}\n\nint main() {\n    // 多次调用 read_data 函数，每次都会泄漏内存\n    for (int i = 0; i < 5; i++) {\n        read_data();\n        printf(\"第 %d 次调用后，内存泄漏未被释放\\n\", i + 1);\n    }\n\n    // 程序结束时，所有通过 malloc 分配的内存都没有释放\n    return 0;\n}\n"
    extra_info = {
    "input_output": "{\n  \"inputs\": [\"1\\n1\\n2\\n2\\n2\\n\" ],\n  \"outputs\": [\n    \"1\\n3 \\n-1\\n0\\n\\n2\\n1 2 \\n\"\n  ]\n}"
}
    res = compute_score("", solution_str, "", extra_info)
    print(res)