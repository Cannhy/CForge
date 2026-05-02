import os
import contextlib
import threading
import subprocess
import tempfile

from typing import Dict
# from process_human_eval import write_jsonl, read_problems


IMPORT_HELPER = {
        "c": [
            "#include<stdlib.h>",
            "#include<stdbool.h>",
            "#include<math.h>",
            "#include<stdio.h>",
            "#include<string.h>",
            "#include<ctype.h>",
            "#include<assert.h>",
            "#include<time.h>",
            "#include<limits.h>",
            "#include<stdint.h>",
            "#include<float.h>"
        ]
}


class TimeoutException(Exception):
    pass


@contextlib.contextmanager
def time_limit(seconds: float):
    timer = threading.Timer(seconds, lambda: _raise_timeout_exception())
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


def _raise_timeout_exception():
    raise TimeoutException("Timed out!")


def run_code_snip(code: str) -> Dict[str, Dict[str, str]]:
    result = {
        "compile_result": {
            "return_code": "",
            "stderr": "",
            "stdout": ""
        },
        "execute_result": {
            "return_code": "",
            "stderr": "",
            "stdout": ""
        }
    }

    test_set_up = ""
    for s in IMPORT_HELPER["c"]:
        if s not in code:
            test_set_up += s + "\n"


    tmp_dir = tempfile.mkdtemp()
    src_path = os.path.join(tmp_dir, "test.c")
    exe_path = os.path.join(tmp_dir, "test.out")

    # 写入 C 代码
    with open(src_path, 'w', encoding='utf-8') as f:
        f.write(test_set_up + '\n' + code)

    # 编译
    try:
        compilation_result = subprocess.run(
            ["gcc", "-std=c11", "-D_POSIX_C_SOURCE=200809L", src_path, "-lm", "-o", exe_path],
            timeout=6,
            capture_output=True
        )
    except Exception as e:
        print("here``````")
        print(e)

    result["compile_result"]["return_code"] = str(compilation_result.returncode)
    result["compile_result"]["stderr"] = compilation_result.stderr.decode(errors="replace")
    result["compile_result"]["stdout"] = compilation_result.stdout.decode(errors="replace")

    if compilation_result.returncode != 0:
        return result

    # 执行
    try:
        exec_result = subprocess.run([exe_path], timeout=4.0, capture_output=True)
        result["execute_result"]["return_code"] = str(exec_result.returncode)
        result["execute_result"]["stderr"] = exec_result.stderr.decode(errors="replace")
        result["execute_result"]["stdout"] = exec_result.stdout.decode(errors="replace")
    except subprocess.TimeoutExpired:
        result["execute_result"]["return_code"] = "timeout"
        result["execute_result"]["stderr"] = "Execution timed out."
        result["execute_result"]["stdout"] = ""

    return result


def run_code(file_path: str):
    ds = read_problems(file_path)
    for x in ds.keys():
        result = []
        sample = ds[x]
        _id = sample['task_id'].split('_')[1]
        code = sample['canonical'] + '\n' + sample['test']
        test_set_up = ""
        print(sample['task_id'] + "start:::")
        # if "#include" in code:
        for s in IMPORT_HELPER["c"]:
            if s not in code:
                test_set_up += s + "\n"
        open(f"../test.c", 'w').write(test_set_up + '\n' + code)
        compilation_result = subprocess.run(["gcc", "-std=c11", "-D_POSIX_C_SOURCE=200809L", "test.c", "-lm"],
                                            timeout=3,
                                            capture_output=True)
        if compilation_result.returncode != 0:
            if compilation_result.stderr:
                err = compilation_result.stderr.decode()
            else:
                err = compilation_result.stdout.decode()
            result.append(f"failed: compilation error: {err}")
        else:
            try:
                exec_result = None
                with time_limit(4.0):
                    exec_result = subprocess.run(["./a.exe"], timeout=4.0, capture_output=True)

                if exec_result.returncode == 0:
                    result.append("passed")
                else:
                    if exec_result.stderr:
                        try:
                            err = exec_result.stderr.decode()
                        except:
                            err = exec_result.stderr
                    else:
                        try:
                            err = exec_result.stdout.decode()
                        except:
                            err = exec_result.stdout
                    result.append(f"failed: {err}")
            except TimeoutException:
                result.append("timed out")
        samp = {}
        samp['result'] = result[0]
        samp['task_id'] = sample['task_id']
        samples = [samp]
        write_jsonl("exec_result.jsonl", samples, True)