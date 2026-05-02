import math
import tempfile
from ctypes import (
    c_int, c_float, c_char_p, c_char,
    POINTER, c_bool, c_longlong, c_long,
    CDLL, c_double
)
import signal
from multiprocessing import Process, Queue
import json
import os
import subprocess
from typing import List, Dict, Any
import faulthandler

from scipy.io._idl import Pointer

faulthandler.enable()

# 类型映射
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
        if c_type == POINTER(POINTER(c_char_p)):  # 二维数组
            n = len(data)
            arr_type = POINTER(c_char_p) * n  # 创建二维数组类型
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
            arr = (c_double * len(data))(*data)  # 将 float 数组转换为 double 数组
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
            # 对于单个char，ctypes通常是bytes类型（长度为1），或者是int
            if isinstance(c_data, bytes) and len(c_data) == 1:
                return c_data.decode('utf-8')
            elif isinstance(c_data, int):  # 当以数值方式传递
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

def compile_c_code(c_source: str, output_lib: str) -> (bool, str):
    """编译C代码，安全保存源代码和目标库"""
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

def universal_c_tester(
        c_code: str,
        func_name: str,
        signature: Dict,
        case: Dict,
        lib_path: str = "solution.so"
) -> Dict[str, Any]:
    tmp_dir = tempfile.mkdtemp()
    lib_path = os.path.join(tmp_dir, lib_path)
    flag, msg = compile_c_code(c_code, lib_path)
    if not flag:
        return {"status": "compile_error", "results": {"passed": False}, "msg": msg}

    try:
        lib = CDLL(lib_path)
        func = configure_function(lib, func_name, signature)

        results = []
        # for case in test_cases:
        try:
            raw_inputs = list(case["input"])
            c_args = []
            i = 0
            while i < len(func.argtypes):
                expected_type = func.argtypes[i]

                if i >= len(raw_inputs):
                    raise ValueError(f"Missing input for argument {i}")

                arg_val = raw_inputs[i]

                # int**（二维数组）
                if expected_type == POINTER(POINTER(c_int)) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    # 自动补行数
                    raw_inputs.insert(i + 1, len(arg_val))

                    # 自动补列数数组
                    if len(arg_val) > 0 and isinstance(arg_val[0], list):
                        raw_inputs.insert(i + 2, [len(row) for row in arg_val])

                    i += 1

                # int*（一维数组）
                elif expected_type == POINTER(c_int) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    # ✅ 无论如何都插入长度
                    raw_inputs.insert(i + 1, len(arg_val))
                    i += 1

                # longlong*（一维数组）
                elif expected_type == POINTER(c_longlong) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    raw_inputs.insert(i + 1, len(arg_val))
                    i += 1
                # longlong**（二维数组）
                elif expected_type == POINTER(POINTER(c_longlong)) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    raw_inputs.insert(i + 1, len(arg_val))  # 补行数
                    if len(arg_val) > 0 and isinstance(arg_val[0], list):
                        first_row_length = len(arg_val[0])
                        raw_inputs.insert(i + 2, first_row_length)
                    i += 1

                # long**（二维数组）
                elif expected_type == POINTER(POINTER(c_long)) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    raw_inputs.insert(i + 1, len(arg_val))  # 补行数
                    # if len(arg_val) > 0 and isinstance(arg_val[0], list):
                    #     raw_inputs.insert(i + 2, [len(row) for row in arg_val])
                    if len(arg_val) > 0 and isinstance(arg_val[0], list):
                        first_row_length = len(arg_val[0])
                        raw_inputs.insert(i + 2, first_row_length)  # 改为单个int值
                    i += 1

                # long*（一维数组）
                elif expected_type == POINTER(c_long) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    raw_inputs.insert(i + 1, len(arg_val))
                    i += 1

                # char***（三维数组）
                elif expected_type == POINTER(POINTER(c_char_p)) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    # 自动补充行数
                    raw_inputs.insert(i + 1, len(arg_val))

                    i += 1

                # char**（字符串数组）
                elif expected_type == POINTER(c_char_p) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))

                    # ✅ 也统一插入长度
                    raw_inputs.insert(i + 1, len(arg_val))
                    i += 1
                elif expected_type == POINTER(c_double) and isinstance(arg_val, list):
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                    raw_inputs.insert(i + 1, len(arg_val))
                    i += 1
                else:
                    # 普通类型
                    c_args.append(CTypeConverter.python_to_c(arg_val, expected_type))
                    i += 1

            # 调用函数
            ret = func(*c_args)

            # 输出处理
            output = None
            ret_spec = signature["return"]
            # if ret_spec["type"] == "char**":
            #     print(ret[0].decode('utf-8'))
            #     output = CTypeConverter.c_to_python(ret, "char**", length)
            if ret_spec["type"] == "array":
                length = len(case["output"])
                dim = ret_spec.get("dimension", 1)
                if ret_spec.get("element_type") == "char":
                    if dim == 1:
                        output = CTypeConverter.c_to_python(ret, "char*", length)
                    else:
                        output = CTypeConverter.c_to_python(ret, "char**", length)
                elif ret_spec["element_type"] == "double" or ret_spec["element_type"] == "float":
                    if dim == 1:
                        output = CTypeConverter.c_to_python(ret, "double[]", length)
                    else:
                        output = CTypeConverter.c_to_python(ret, "double[][]", length)
                else:
                    if dim == 2:
                        output = CTypeConverter.c_to_python(ret, "int[][]", length)
                    else:
                        output = CTypeConverter.c_to_python(ret, "int[]", length)
            else:
                output = CTypeConverter.c_to_python(ret, ret_spec["type"])

            passed = False
            if ret_spec["type"] == "double" or ret_spec["type"] == "float":
                if math.isclose(output, case['output'], rel_tol=1e-3, abs_tol=1e-3):
                    passed = True
            else:
                passed = (output == case["output"])

            results.append({
                "input": case["input"],
                "output": output,
                "expected": case["output"],
                "passed": passed
            })

        except Exception as e:
            results.append({
                "input": case["input"],
                "error": str(e),
                "passed": False
            })

        return {"status": "success", "results": results[0]}
    finally:
        if os.path.exists(lib_path):
            os.remove(lib_path)

if __name__ == "__main__":
    matrix_rotate_config = {
        'args': ['char*'], 'return': {'type': 'long long'}
    }

    matrix_rotate_c_code = """
#include <stdio.h>
#include <string.h>
#include <limits.h>

// Helper function to check if a number formed by two digits is divisible by 25
int isDivisibleBy25(char a, char b) {
    if (a == '0' && (b == '0' || b == '5')) return 1;
    if (a == '2' && b == '5') return 1;
    if (a == '5' && (b == '0' || b == '5')) return 1;
    if (a == '7' && b == '5') return 1;
    return 0;
}

long long minimumOperationsToMakeSpecial(char* num) {
    int n = strlen(num);
    long long minOps = LLONG_MAX;

    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (isDivisibleBy25(num[i], num[j])) {
                long long curOps = n - 2;
                for (int k = 0; k < i; k++) {
                    if (num[k] != '0') {
                        curOps++;
                    }
                }
                for (int k = i + 1; k < j; k++) {
                    curOps++;
                }
                for (int k = j + 1; k < n; k++) {
                    curOps++;
                }
                minOps = curOps < minOps ? curOps : minOps;
            }
        }
    }

    if (minOps == LLONG_MAX) {
        // If no two - digit combination divisible by 25 is found, we need to delete all digits
        minOps = n;
    }
    return minOps;
}
"""
    test_cases = {
        "input": ["2245047"],
        "output": 2
    }

    result = universal_c_tester(
        c_code=matrix_rotate_c_code,
        func_name="minimumOperationsToMakeSpecial",
        signature=matrix_rotate_config,
        case=test_cases
    )
    print(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))