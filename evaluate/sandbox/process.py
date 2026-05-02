import gzip
import json
import os

from typing import Iterable, Dict


def read_problems(evalset_file) -> Dict[str, Dict]:
    result = {}
    for task in stream_jsonl(evalset_file):  # 假设 stream_jsonl 是一个生成器，逐行读取 JSONL 文件
        if "task_id" in task:  # 检查 task 是否存在 "task_id" 键
            result[task["task_id"]] = task
        else:
            result[task["name"]] = task
    return result
    # return {task["task_id"]: task for task in stream_jsonl(evalset_file)}


# def stream_jsonl(filename: str) -> Iterable[Dict]:
#     """
#     Parses each jsonl line and yields it as a dictionary
#     """
#     if filename.endswith(".gz"):
#         with open(filename, "rb", encoding='utf-8') as gzfp:
#             with gzip.open(gzfp, 'rt') as fp:
#                 for line in fp:
#                     if any(not x.isspace() for x in line):
#                         yield json.loads(line)
#     else:
#         with open(filename, "r", encoding='utf-8') as fp:
#             for line in fp:
#                 if any(not x.isspace() for x in line):
#                     yield json.loads(line)

def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary.
    Logs line number and content if JSONDecodeError occurs.
    """
    def read_lines(fp):
        for line_num, line in enumerate(fp, 1):
            if any(not x.isspace() for x in line):
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSONDecodeError at line {line_num}:")
                    print(f"--> {line.strip()}")
                    raise e

    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, 'rt', encoding='utf-8') as fp:
                yield from read_lines(fp)
    else:
        with open(filename, "r", encoding='utf-8') as fp:
            yield from read_lines(fp)


def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to jsonl
    """
    if append:
        mode = 'ab'
    else:
        mode = 'wb'
    filename = os.path.expanduser(filename)
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode='wb') as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x, ensure_ascii=True) + "\n").encode('utf-8'))
    else:
        with open(filename, mode) as fp:
            for x in data:
                fp.write((json.dumps(x, ensure_ascii=True) + "\n").encode('utf-8'))
