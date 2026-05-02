import math
import tempfile
import signal
import json
import faulthandler
import os
import subprocess
import time

from multiprocessing import Process, Queue
from typing import List, Dict, Any
from multiprocessing import Process, Queue
from ctypes import (
    c_int, c_float, c_char_p, c_char,
    POINTER, c_bool, c_longlong, c_long,
    CDLL, c_double
)

faulthandler.enable()

TYPE_MAPPING = {
    "int": c_int,
    "bool": c_bool,
    "float": c_float,
    "char": c_char,
    "char*": c_char_p,
    "char**": POINTER(c_char_p),
    "char***": POINTER(POINTER(c_char_p)),
    "int*": POINTER(c_int),
    "int**": POINTER(POINTER(c_int)),
    "float*": POINTER(c_float),
    "float**": POINTER(POINTER(c_float)),
    "double": c_double,
    "double*": POINTER(c_double),
    "double**": POINTER(POINTER(c_double)),
    "long": c_long,
    "long*": POINTER(c_long),
    "long**": POINTER(POINTER(c_long)),
    "long long": c_longlong,
    "long long*": POINTER(c_longlong),
    "long long**": POINTER(POINTER(c_longlong))
}


class CTypeConverter:
    @staticmethod
    def python_to_c(data: Any, c_type: Any):
        if c_type == c_char_p:
            return data.encode() if isinstance(data, str) else data
        elif c_type == c_int:
            return int(data)
        elif c_type == c_float:
            return float(data)
        elif c_type == c_bool:
            return bool(data)
        elif c_type == c_char:
            if isinstance(data, str) and len(data) == 1:
                return data.encode('utf-8')
            elif isinstance(data, bytes) and len(data) == 1:
                return data  # 原本就是 b'a'
            elif isinstance(data, int):  # 如果是 ASCII 值
                return data
            else:
                raise TypeError(f"c_char expects a single character (str, bytes) or an integer, got: {data}")
        elif c_type == c_longlong:
            return int(data)

        # int**
        if c_type == POINTER(POINTER(c_int)):
            n = len(data)
            arr_type = POINTER(c_int) * n
            c_array = arr_type()
            for i, row in enumerate(data):
                row_type = c_int * len(row)
                c_array[i] = row_type(*row)
            return c_array

        # char**
        if c_type == POINTER(c_char_p):
            return (c_char_p * len(data))(*[s.encode() for s in data])
        # char***
        if c_type == POINTER(POINTER(c_char_p)):
            n = len(data)
            arr_type = POINTER(c_char_p) * n
            c_array = arr_type()
            for i, row in enumerate(data):
                c_array[i] = (c_char_p * len(row))(*[c_char_p(s.encode()) for s in row])
            return c_array
        # longlong**
        if c_type == POINTER(POINTER(c_longlong)):
            n = len(data)
            arr_type = POINTER(c_longlong) * n
            c_array = arr_type()
            for i, row in enumerate(data):
                row_type = c_longlong * len(row)
                c_array[i] = row_type(*row)
            return c_array
        # longlong*
        if c_type == POINTER(c_longlong):
            arr = (c_longlong * len(data))(*data)
            return arr
        # int*
        if c_type == POINTER(c_int):
            arr = (c_int * len(data))(*data)
            return arr

            # double*
        if c_type == POINTER(c_double):
            arr = (c_double * len(data))(*data)
            return arr

        return data

    @staticmethod
    def c_to_python(c_data, py_type: str, length=None):
        if py_type == "int":
            return int(c_data)
        elif py_type == "float":
            return float(c_data)
        elif py_type == "double":
            return float(c_data)
        elif py_type == "str" or py_type == "char*":
            if not c_data:
                return ""
            if isinstance(c_data, bytes):
                return c_data.decode('utf-8')
            else:
                return str(c_data)
        elif py_type == "int[]":
            return [c_data[i] for i in range(length)]
        elif py_type == "char**":
            if not c_data or length is None:
                return []
            return [c_data[i].decode() if c_data[i] else "" for i in range(length)]
        elif py_type == "int[][]":
            return [[c_data[i][j] for j in range(length)] for i in range(length)]
        elif py_type == "double[]":
            return [float(c_data[i]) for i in range(length)]
        elif py_type == "double[][]":
            return [[float(c_data[i][j]) for j in range(length)] for i in range(length)]
        elif py_type == "bool":
            return bool(c_data)
        elif py_type == "long long":
            return int(c_data)
        elif py_type == "char":
            if isinstance(c_data, bytes) and len(c_data) == 1:
                return c_data.decode('utf-8')
            elif isinstance(c_data, int):
                return chr(c_data)
            else:
                return str(c_data)
        elif py_type == "char***":
            if not c_data or length is None:
                return []

            return [
                [
                    [
                        c_data[i][j][k].decode() if c_data[i][j][k] else ""
                        for k in range(len(c_data[i][j]))
                    ]
                    for j in range(len(c_data[i]))
                ]
                for i in range(len(c_data))
            ]


class TimeoutException(Exception):
    pass


def compile_c_code(c_source: str, output_lib: str) -> (bool, str):
    src_dir = os.path.dirname(output_lib)

    try:
        # 创建源代码文件
        c_source = c_source.replace("\\n", '\n')
        c_source = c_source.replace("\\'", "'")
        c_source = c_source.replace('\\"', '"')
        src_file = os.path.join(src_dir, "temp_solution.c")
        with open(src_file, "w") as f:
            f.write(c_source)

        subprocess.run(["gcc", "-shared", "-o", output_lib, "-fPIC", src_file],
                       check=True, stderr=subprocess.PIPE)

        return True, "success"

    except subprocess.CalledProcessError as e:
        msg = f"Compilation failed: {e.stderr.decode()}"
        return False, msg

    finally:
        if os.path.exists(src_file):
            os.remove(src_file)


def configure_function(lib, func_name: str, signature: Dict):
    try:
        func = getattr(lib, func_name)
        func.argtypes = [TYPE_MAPPING[arg] for arg in signature["args"]]
        ret_type = signature["return"]
        dim = ret_type.get("dimension", 1)
        if ret_type["type"] == "array":
            ele_type = ret_type["element_type"]
            if ele_type == "char":
                if dim == 1:
                    func.restype = c_char_p
                else:
                    func.restype = POINTER(c_char_p)
            else:
                elem = TYPE_MAPPING[ele_type]
                func.restype = POINTER(POINTER(elem)) if dim == 2 else POINTER(elem)
        else:
            func.restype = TYPE_MAPPING[ret_type["type"]]
        return func
    except AttributeError:
        raise AttributeError(f"Function {func_name} not found in library")
    except KeyError as e:
        raise ValueError(f"Unsupported type in signature: {e}")


def _run_c_function_execution(lib_path, func_name, signature, case, result_queue):
    error_template = {
        "input": case["input"],
        "expected": case["output"]
    }

    try:
        lib = CDLL(lib_path)
        func = configure_function(lib, func_name, signature)

        raw_inputs = list(case["input"])
        c_args = []
        i = 0
        while i < len(func.argtypes):
            expected_type = func.argtypes[i]
            if i >= len(raw_inputs):
                raise ValueError(f"Missing input for argument {i}")

            arg_val = raw_inputs[i]
            # 完成参数类型检查和构建
            if expected_type == POINTER(POINTER(c_int)) and isinstance(arg_val, list):  # int**
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                if len(arg_val) > 0 and isinstance(arg_val[0], list):
                    raw_inputs.insert(i + 2, [len(row) for row in arg_val])
                i += 1
            elif expected_type == POINTER(c_int) and isinstance(arg_val, list):  # int*
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                i += 1
            elif expected_type == POINTER(c_longlong) and isinstance(arg_val, list):  # long long*
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                i += 1
            elif expected_type == POINTER(POINTER(c_longlong)) and isinstance(arg_val, list):  # long long**
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                if len(arg_val) > 0 and isinstance(arg_val[0], list):
                    raw_inputs.insert(i + 2, len(arg_val[0]))
                i += 1
            elif expected_type == POINTER(POINTER(c_long)) and isinstance(arg_val, list):  # long**
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                if len(arg_val) > 0 and isinstance(arg_val[0], list):
                    raw_inputs.insert(i + 2, len(arg_val[0]))
                i += 1
            elif expected_type == POINTER(c_long) and isinstance(arg_val, list):  # long*
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                i += 1
            elif expected_type == POINTER(c_char_p) and isinstance(arg_val, list):  # char**
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                i += 1
            elif expected_type == POINTER(POINTER(c_char_p)) and isinstance(arg_val, list):  # char***
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                i += 1
            elif expected_type == POINTER(c_double) and isinstance(arg_val, list):  # double*
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                raw_inputs.insert(i + 1, len(arg_val))
                i += 1
            else:
                c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                i += 1

        start_time = time.time()
        ret = func(*c_args)
        end_time = time.time()
        total_execution_time = end_time - start_time

        ret_spec = signature["return"]

        length = len(case["output"]) if isinstance(case["output"], (list, tuple)) else None

        if ret_spec["type"] == "array":
            dim = ret_spec.get("dimension", 1)
            if ret_spec.get("element_type") == "char":
                output = CTypeConverter.c_to_python(ret, "char*" if dim == 1 else "char**", length)
            elif ret_spec["element_type"] in ("double", "float"):
                output = CTypeConverter.c_to_python(ret, "double[]" if dim == 1 else "double[][]", length)
            else:
                output = CTypeConverter.c_to_python(ret, "int[]" if dim == 1 else "int[][]", length)
        else:
            output = CTypeConverter.c_to_python(ret, ret_spec["type"])

        passed = False
        if ret_spec["type"] in ("double", "float"):
            passed = math.isclose(output, case["output"], rel_tol=1e-3, abs_tol=1e-3)
        else:
            passed = (output == case["output"])

        if not passed:
            error_template["error_code"] = -2
            error_template["error_message"] = "Wrong Answer"
            result_queue.put(([-2], error_template))
        else:
            result_queue.put(([True], {"execution_time": total_execution_time, "output": output}))

    except Exception as e:
        error_template["error_code"] = -4
        error_template["error_message"] = str(e)
        result_queue.put(([-4], error_template))


def universal_c_tester(
        c_code: str,
        func_name: str,
        signature: Dict,
        case: Dict,
        lib_path_base: str = "solution",
        timeout: int = 1,
):
    results = []
    error_template = {
        "input": case["input"],
        "expected": case["output"]
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        lib_file = os.path.join(tmp_dir, f"{lib_path_base}_{os.getpid()}_{time.time_ns()}.so")

        compiled, compile_msg = compile_c_code(c_code, lib_file)
        if not compiled:
            return [-1], {"error_code": -1, "error_message": "Compile Error", "output": compile_msg, **error_template}

        result_queue = Queue()
        process = Process(target=_run_c_function_execution, args=(lib_file, func_name, signature, case, result_queue))
        process.start()
        process.join(timeout=timeout)

        if process.is_alive():
            process.terminate()
            process.join()
            error_template["error_code"] = -3
            error_template["error_message"] = "Time Limit Exceeded (Execution)"
            return [-3], error_template
        else:
            if not result_queue.empty():
                return_val = result_queue.get()
                if isinstance(return_val[0], list) and return_val[0][0] == -2:
                    error_template["error_code"] = -2
                    error_template["error_message"] = "Wrong Answer"
                    error_template["output"] = return_val[1].get("output", "N/A")
                    return [-2], error_template
                elif isinstance(return_val[0], list) and return_val[0][0] == -4:
                    error_template["error_code"] = -4
                    error_template["error_message"] = f"Runtime Error: {return_val[1].get('error_message', 'Unknown')}"
                    return [-4], error_template
                else:
                    return return_val
            else:
                error_template["error_code"] = -5
                error_template["error_message"] = "Unexpected process termination or no result in queue."
                return [-5], error_template

if __name__ == "__main__":
    matrix_rotate_config = {
        'args': ['char*', 'char***', 'int', 'double*', 'int', 'char***', 'int', 'double*', 'int'],
        'return': {'type': 'double'}
    }

    matrix_rotate_c_code = """
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_CURRENCY 20  // 增加货币数量上限
#define INF 1e18

// 辅助函数：获取货币的编号
int getCurrencyIndex(char* currency, char** currencyList, int currencyCount) {
    for (int i = 0; i < currencyCount; i++) {
        if (strcmp(currency, currencyList[i]) == 0) {
            return i;
        }
    }
    return -1;
}

// 主函数：计算最大金额
double maxFinalAmount(
    char* initialCurrency, 
    char*** pairs1, int pairs1Size, double* rates1, int rates1Size, 
    char*** pairs2, int pairs2Size, double* rates2, int rates2Size) 
{
     for (int i = 0; i < pairs2Size;) {
     }
    // 存储所有货币的名称，用于货币编号
    char* currencies[MAX_CURRENCY];
    int currencyCount = 0;

    // 记录所有货币并生成编号
    for (int i = 0; i < pairs1Size; i++) {
        if (getCurrencyIndex(pairs1[i][0], currencies, currencyCount) == -1) {
            currencies[currencyCount++] = pairs1[i][0];
        }
        if (getCurrencyIndex(pairs1[i][1], currencies, currencyCount) == -1) {
            currencies[currencyCount++] = pairs1[i][1];
        }
    }

    for (int i = 0; i < pairs2Size; i++) {
        if (getCurrencyIndex(pairs2[i][0], currencies, currencyCount) == -1) {
            currencies[currencyCount++] = pairs2[i][0];
        }
        if (getCurrencyIndex(pairs2[i][1], currencies, currencyCount) == -1) {
            currencies[currencyCount++] = pairs2[i][1];
        }
    }

    // 构建两天的转换图
    double graph1[currencyCount][currencyCount];
    double graph2[currencyCount][currencyCount];
    for (int i = 0; i < currencyCount; i++) {
        for (int j = 0; j < currencyCount; j++) {
            graph1[i][j] = -INF;
            graph2[i][j] = -INF;
        }
    }

    // 初始化第1天的转换图
    for (int i = 0; i < pairs1Size; i++) {
        int u = getCurrencyIndex(pairs1[i][0], currencies, currencyCount);
        int v = getCurrencyIndex(pairs1[i][1], currencies, currencyCount);
        graph1[u][v] = rates1[i];
        graph1[v][u] = 1.0 / rates1[i];
    }

    // 初始化第2天的转换图
    for (int i = 0; i < pairs2Size; i++) {
        int u = getCurrencyIndex(pairs2[i][0], currencies, currencyCount);
        int v = getCurrencyIndex(pairs2[i][1], currencies, currencyCount);
        graph2[u][v] = rates2[i];
        graph2[v][u] = 1.0 / rates2[i];
    }

    // 动态规划数组：记录每种货币的最大金额
    double dp1[currencyCount];  // 第1天后的最大金额
    double dp2[currencyCount];  // 第2天后的最大金额
    for (int i = 0; i < currencyCount; i++) {
        dp1[i] = -INF;
        dp2[i] = -INF;
    }

    // 初始货币的最大金额为 1.0
    int startIdx = getCurrencyIndex(initialCurrency, currencies, currencyCount);
    dp1[startIdx] = 1.0;

    // 第1天的转换
    for (int k = 0; k < currencyCount; k++) {
        for (int i = 0; i < currencyCount; i++) {
            if (dp1[i] > -INF) {
                for (int j = 0; j < currencyCount; j++) {
                    if (graph1[i][j] > -INF) {
                        dp1[j] = fmax(dp1[j], dp1[i] * graph1[i][j]);
                    }
                }
            }
        }
    }

    // 第2天的转换（基于第1天的结果）
    for (int i = 0; i < currencyCount; i++) {
        dp2[i] = dp1[i];  // 初始化为第1天的结果
    }
    for (int k = 0; k < currencyCount; k++) {
        for (int i = 0; i < currencyCount; i++) {
            if (dp2[i] > -INF) {
                for (int j = 0; j < currencyCount; j++) {
                    if (graph2[i][j] > -INF) {
                        dp2[j] = fmax(dp2[j], dp2[i] * graph2[i][j]);
                    }
                }
            }
        }
    }

    // 返回最终的最大金额
    double maxAmount = 0;
    for (int i = 0; i < currencyCount; i++) {
        maxAmount = fmax(maxAmount, dp2[i]);
    }

    return maxAmount;
}
"""
    test_cases = {
        "input": ["EUR", [["EUR", "USD"], ["USD", "JPY"]], [2.0, 3.0], [["JPY", "USD"], ["USD", "CHF"], ["CHF", "EUR"]],
                  [4.0, 5.0, 6.0]],
        "output": 720.0
    }

    result = universal_c_tester(
        c_code=matrix_rotate_c_code,
        func_name="maxFinalAmount",
        signature=matrix_rotate_config,
        case=test_cases
    )
    print(result)
    # print(json.dumps(result, indent=2, ensure_ascii=False))