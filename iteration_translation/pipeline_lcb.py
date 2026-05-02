import os
import re
import json
import time
import yaml
import logging
import traceback

from datetime import datetime
from typing import List, Optional

from iteration_translation.process_human_eval import read_problems_dict
from iteration_translation.sandbox.sandbox import *
from collections import defaultdict
from threading import Lock
from few_shots import translate_lcb_call_based_shots
from tqdm.auto import tqdm
from template import translate_lcb_template
from LLM_adapter import LLMAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from process_human_eval import write_jsonl, read_problems
from t_c_types import *
from multiprocessing import Process, Queue, get_context


timestamp = f"2025-06-21-3763"
log_filename = f"./logs/run_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    filename=log_filename,  # 写入文件
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

write_lock = Lock()


def load_config(config_path: str = "./config/config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


llm = LLMAdapter()
config = load_config()
ai_cop, model_name = config['active_model']['series'], config['active_model']['model_name']


class Sample:
    def __init__(self, question_id, py_prompt="", py_sig="", py_code="", py_test="", input_out=None, c_code="", c_config = "", c_signature = ""):
        self.question_id = question_id
        self.py_prompt = py_prompt
        self.py_signature = py_sig
        self.py_code = py_code
        self.py_testcase = py_test
        self.input_out = input_out

        self.c_prompt = ""
        self.c_signature = c_signature
        self.c_code = c_code
        self.c_config = c_config

        self.retry_cnt = -1
        self.final_result = "failed"
        self.pass_rate = 0
        self.error = ""

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "question_content": self.c_prompt,
            "starter_code": self.c_signature,
            "solution": self.c_code,
            "config": self.c_config,
            "retry_cnt": self.retry_cnt,
            "final_result": self.final_result,
            "pass_rate": self.pass_rate,
            "error": self.error,
        }


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)
    return conf


def check_un_dealt():
    full_set = set(range(11, 511))
    dataset_path = config['dataset']['backup']
    dataset_dict = read_problems(dataset_path)
    handled_set = {sample['task_id'] for sample in dataset_dict.values()}
    unhandled_ids = sorted(full_set - handled_set)
    print(f"Unhandled task_ids: {unhandled_ids}")


def extract_function_name(signature_code: str) -> str:
    match = re.search(r'\s*\w+\s*[*&]*\s+(\w+)\s*\(', signature_code)
    return match.group(1) if match else ""


def check_duplicate_ids():
    dataset_path = config['dataset']['output']
    dataset_dict = read_problems(dataset_path)

    counter = defaultdict(int)
    for sample in dataset_dict.values():
        counter[sample['question_id']] += 1

    duplicates = {k: v for k, v in counter.items() if v > 1}
    if duplicates:
        print("Duplicate task_ids found:")
        for task_id, count in sorted(duplicates.items()):
            print(f"  task_id {task_id} appears {count} times")
    else:
        print("No duplicate task_ids found.")


def build_prompt(
    sample: Sample,
    few_shot_examples: List[Dict[str, str]],
    previous_c_code: Optional[str] = None,
    previous_c_config: Optional[str] = None,
    run_feedback: Optional[str] = None
) -> str:
    return translate_lcb_template.render(
        k=len(few_shot_examples),
        examples=few_shot_examples,
        target_python_prompt=sample.py_prompt,
        target_python_signature=sample.py_signature,
        target_python_test=sample.py_testcase,
        previous_c_code=previous_c_code,
        previous_c_config=previous_c_config,
        run_feedback=run_feedback
    )


def extract_between_tags(text: str, start_tag: str, end_tag: str = None) -> str:
    start_pos = text.find(f"[{start_tag}]")
    if start_pos == -1:
        return ""

    start_pos += len(f"[{start_tag}]")

    if end_tag:
        end_pos = text.find(f"[{end_tag}]", start_pos)
        if end_pos == -1:
            return text[start_pos:].strip()
        return text[start_pos:end_pos].strip()
    else:
        return text[start_pos:].strip()


def format_run_result_as_feedback(run_result, max_cases=5, max_case_chars=1500, max_total_chars=10000) -> str:
    if run_result[0]['status'] == "compile_error":
        return run_result[0]['msg']
    failed_cases = [r['results'] for r in run_result if not r['results'].get('passed')]
    if not failed_cases:
        return "All test cases passed."

    feedback_lines = [f"Some test cases failed. Showing up to {max_cases} failed cases."]

    for idx, case in enumerate(failed_cases[:max_cases]):
        input_str = json.dumps(case.get("input"), ensure_ascii=False)
        expected = json.dumps(case.get("expected"), ensure_ascii=False)
        actual = json.dumps(case.get("output", case.get("error", "")), ensure_ascii=False)

        case_feedback = f"- Case {idx + 1}:\n  Input: {input_str}\n  Expected: {expected}\n  Got: {actual}"

        if len(case_feedback) > max_case_chars:
            case_feedback = case_feedback[:max_case_chars] + "\n  (truncated...)"

        feedback_lines.append(case_feedback)

    final_feedback = "\n".join(feedback_lines)

    if len(final_feedback) > max_total_chars:
        final_feedback = final_feedback[:max_total_chars] + "\n...(feedback truncated overall)"
    # logging.info("[final feedback]: %s", final_feedback)
    return final_feedback


def sample_to_dict(sample: Sample) -> Dict:
    return {
        "question_id": sample.question_id,
        "question_content": sample.c_prompt,
        "starter_code": sample.c_signature,
        "solution": sample.c_code,
        "config": sample.c_config,
    }


def sandbox_run(func_name: str, code: str, param_config: Dict, input_out: List[str], _id: int = 0) -> List[Dict]:
    input_out_str = input_out[0]
    input_out_dict = json.loads(input_out_str)
    results = []

    for gt_in, gt_out in zip(input_out_dict["inputs"], input_out_dict["outputs"]):
        if int(_id) == 3235:
            lines = [json.loads(line) for line in gt_in.strip().splitlines()]
            # lines[0] -> "abcd" lines[1] -> "acbe" lines[2] -> ["a", "b", "c", "c", "e", "d"] lines[3] -> ["b", "c", "b", "e", "b", "e"] lines[4] -> [2, 5, 5, 1, 2, 20]
            test_case = {
                "input": [
                    lines[0],
                    lines[1],
                    ''.join(lines[2]),  # 原来是列表，合成字符串
                    ''.join(lines[3]),
                    lines[4]
                ],
                "output": json.loads(gt_out)
            }
        elif int(_id) == 3492:
            gt_in_json = json.loads(gt_in)
            test_case = {
                "input": [["".join(row) for row in gt_in_json]],
                "output": json.loads(gt_out)
            }
        elif int(_id) == 3398:
            gt_in_json = json.loads(gt_in)
            test_case = {
                "input": [["".join(row) for row in gt_in_json]],
                "output": json.loads(gt_out)
            }
        else:
            test_case = {
            "input": [json.loads(line) for line in gt_in.strip().splitlines()],
            "output": json.loads(gt_out)
            }

        try:
            result = _execute_test_case(
                func_name=func_name,
                code=code,
                param_config=param_config,
                test_case=test_case
            )
            results.append(result)
        except TimeoutError:
            results.append({
                "status": "timeout",
                "results": {
                    "input": test_case["input"],
                    "error": "Execution timed out after 5 seconds",
                    "passed": False
                }
            })
        except Exception as e:
            results.append({
                "status": "error",
                "results": {
                    "input": test_case["input"],
                    "error": f"{str(e)}\n{traceback.format_exc()}",
                    "passed": False
                }
            })

    return results


def _execute_test_case(func_name: str, code: str, param_config: Dict, test_case: Dict) -> Dict:
    """执行单个测试用例（带5秒超时）"""
    ctx = get_context('spawn')
    result_queue = ctx.Queue()

    # 将必要参数打包成元组
    args = (func_name, code, param_config, test_case, result_queue)

    p = ctx.Process(target=_worker_function, args=args)
    p.start()
    p.join(timeout=100)

    if p.is_alive():
        p.terminate()
        p.join()
        raise TimeoutError()

    if not result_queue.empty():
        return result_queue.get()

    raise RuntimeError("No result returned from worker process")


def _worker_function(func_name: str, code: str, param_config: Dict, test_case: Dict, result_queue: Queue):
    """工作进程实际执行的函数（必须定义在模块级别）"""
    try:
        result = universal_c_tester(
            c_code=code,
            func_name=func_name,
            signature=param_config,
            case=test_case
        )
        result_queue.put(result)
    except Exception as e:
        result_queue.put({
            "status": "error",
            "results": {
                "input": test_case["input"],
                "error": str(e),
                "passed": False
            }
        })

def process_sample(sample: Sample,
                   few_shot_examples: List[Dict],
                   retry_cnt: int = 10,
                   output_path: str = "",
                   sample_debug: Sample = None,
                   debug: bool = True,
                   ):
    try:
        prompt = build_prompt(sample, few_shot_examples)
        #logging.info(f'[task_id]: {sample.task_id}, [prompt 0]: {prompt}')
        #time.sleep(1000)
        if not debug:
            model_output = llm.completion(ai_cop=ai_cop, model_name=model_name, prompt=prompt)
            # logging.info(f'[question_id]: {sample.question_id}, [generation 0]:\n {model_output}')
            generated_signature = extract_between_tags(model_output, "signature", "code")
            generated_code = extract_between_tags(model_output, "code", "config")
            generated_config = extract_between_tags(model_output, "config")
            # print(f"[task_id: {sample.task_id}] Extracted Prompt:\n{generated_prompt}")
            # print(f"[task_id: {sample.task_id}] Extracted Signature:\n{generated_signature}")
            # print(f"[task_id: {sample.task_id}] Extracted Code:\n{generated_code}")
            # print(f"[task_id: {sample.task_id}] Extracted Test Case:\n{generated_test}")
            #time.sleep(10000)
            sample.c_signature = generated_signature
            sample.c_code = generated_code
            signature_dict = eval(generated_config)
            sample.c_config = signature_dict
            if signature_dict.get("signature"):
                signature_dict = signature_dict['signature']
            result = sandbox_run(extract_function_name(generated_signature), generated_code, signature_dict,
                                 sample.input_out, _id=sample.question_id)
        else:
            print(type(sample_debug.c_config))
            result = sandbox_run(extract_function_name(sample_debug.c_signature), sample_debug.c_code, (sample_debug.c_config), sample.input_out, _id=sample.question_id)

        # logging.info(f'223 [task_id]: {sample.question_id}, [run_result 0]:\n {result}')
        if not debug:
            if all(r["status"] == "success" and r["results"].get("passed", False) for r in result):
                sample.retry_cnt = 0
                sample.final_result = "success"
                sample.pass_rate = 1
                with write_lock:
                    write_jsonl(output_path, [sample.to_dict()], append=True)
                return sample
        if debug:
            if all(r["status"] == "success" and r["results"].get("passed", False) for r in result):
                sample_debug.retry_cnt = 0
                sample_debug.final_result = "success"
                sample_debug.pass_rate = 1
            else:
                total = len(result)
                passed = sum(1 for r in result if r["status"] == "success" and r["results"].get("passed", False))
                sample_debug.pass_rate = passed / total if total > 0 else 0
                sample_debug.final_result = "failure"
            with write_lock:
                write_jsonl(output_path, [sample_debug.to_dict()], append=True)
            return sample_debug
        for i in range(retry_cnt):
            feedback = format_run_result_as_feedback(result)
            logging.info(feedback)
            prompt = build_prompt(
                sample,
                few_shot_examples,
                previous_c_code=generated_code,
                previous_c_config=generated_config,
                run_feedback=feedback
            )
            # logging.info(prompt)
            model_output = llm.completion(ai_cop=ai_cop, model_name=model_name, prompt=prompt)
            # logging.info(f'245 [task_id]: {sample.question_id}, [generation {i + 1}]:\n {model_output}')

            generated_signature = extract_between_tags(model_output, "signature", "code")
            generated_code = extract_between_tags(model_output, "code", "config")
            generated_config = extract_between_tags(model_output, "config")

            # 从 signature 中提取函数名和签名
            func_name = extract_function_name(generated_signature)
            signature_dict = eval(generated_config)  # 或者使用 safe parser
            if signature_dict.get("signature"):
                signature_dict = signature_dict['signature']
            # 重新运行代码
            result = sandbox_run(func_name, generated_code, signature_dict, sample.input_out, sample.question_id)

            sample.c_signature = generated_signature
            sample.c_code = generated_code
            sample.c_config = generated_config
            sample.retry_cnt = i

            # logging.info(f'265 [task_id]: {sample.question_id}, [run_result {i + 1}]:\n {json.dumps(result, indent=2, ensure_ascii=False)}')

            if all(r["status"] == "success" and r["results"].get("passed", False) for r in result):
                sample.final_result = "success"
                sample.pass_rate = 1
                break
            else:
                total = len(result)
                passed = sum(1 for r in result if r["status"] == "success" and r["results"].get("passed", False))
                sample.pass_rate = passed / total if total > 0 else 0
                sample.final_result = "failure"
        with write_lock:
            write_jsonl(output_path, [sample.to_dict()], append=True)
        return sample
    except Exception as e:
        print(f"Error: {e}")
        sample.error = str(e)
        with write_lock:
            sample.final_result = "error"
            write_jsonl(output_path, [sample.to_dict()], append=True)
        return sample


def main(
        n_workers: int = 4,
        retry_cnt: int = 5,
        out_path: str = "",
        debug: bool = True,
):
    dataset_path = config['dataset']['src_path']
    dataset_dict = read_problems(dataset_path)
    # out_dict = read_problems(out_path)
    # dataset_dict = load_from_disk(dataset_path)
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        # for sample in tqdm(dataset_dict.values()):
        for sample in tqdm(dataset_dict):
            # tmp_code = sample["solutions"]
            # codes = json.loads(tmp_code) if tmp_code != "" else [""]
            sample_obj = Sample(question_id=sample['question_id'], py_prompt=sample['question_content'], py_test=sample['public_test_cases'], input_out=sample['input_output'])
            sample_obj.c_prompt = sample['question_content']
            sample_obj.c_code = sample['solution']
            sample_obj.c_config = sample['config']
            sample_obj.c_signature = sample['starter_code']
            # if 2824 < int(sample_obj.question_id) < 3000:
            # if 0 <= int(sample['question_id']) < 4000:
            if str(sample['question_id']).isdigit() and int(sample['question_id']) in [2834]:
                # sample_debug = findOut(int(sample['question_id']), out_dict)
                args = (sample_obj, translate_lcb_call_based_shots, retry_cnt, out_path, sample_obj, debug)
                future = executor.submit(process_sample, *args)
                futures.append(future)
                break
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing samples"):
        try:
            result = future.result()
            print(result.to_dict())
        except Exception as e:
            print(f"Error processing a sample: {e}")
    print(f"All results written to {config['dataset']['output']}")

def findOut(question_id: int, out_dict):
    for sample in out_dict:
        if int(sample['question_id']) == question_id:
            return Sample(question_id=question_id, c_code=sample['solution'], c_config=sample['config'], c_signature=sample['starter_code'])

def check_correctness():
    c_path = config['dataset']['output']
    c_dict = read_problems(c_path)
    output_path = "./mbpp/mbpp_run_result.jsonl"
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for sample in tqdm(c_dict.values()):
            code = str(sample['c_code'] + '\n' + sample['c_testcase'])
            # args = code
            future = executor.submit(run_code_snip, code)
            futures.append(future)
    for future in tqdm(as_completed(futures), total=len(futures), desc="Running samples"):
        try:
            result = future.result()
            if result['execute_result']['return_code'] != "0":
                print(f"Sample {result['task_id']} is failed.")
            with write_lock:
                write_jsonl(output_path, [{"result": format_run_result_as_feedback(result)}], append=True)
        except Exception as e:
            print(f"Error processing a sample: {e}")
    print(f"All results written to {config['dataset']['output']}")

def check_leak():
    src_path = config['dataset']['src_path']
    out_path = config['dataset']['output']
    src_dic = read_problems_dict(src_path)
    out_dic = read_problems_dict(out_path)
    result = []
    for sample_id, sample_c in out_dic.items():
        if sample_c.get("pass_rate", 100) == 0:
        # if sample_c.get("error", "") != '':
            # print(f"Sample {sample_id} is failed.")
            result.append(int(sample_id))
    print(result)
    # print(len(src_dic))

def remove_error():
    out_path = config['dataset']['output']
    new_path = os.environ.get("LCB_CLEANED_OUTPUT", out_path.replace(".jsonl", "_clean.jsonl"))
    out_dic = read_problems_dict(out_path)
    result = []
    for sample_id, sample_c in out_dic.items():
        if sample_c.get("error", "") == "":
            # print(f"Sample {sample_id} is failed.")
            write_jsonl(new_path, [sample_c], append=True)
        else:
            result.append(int(sample_id))
    print(result)

def remove_spec():
    out_path = config['dataset']['output']
    out_dic = read_problems_dict(out_path)
    new_path = os.environ.get("LCB_CLEANED_OUTPUT", out_path.replace(".jsonl", "_clean.jsonl"))
    for sample_id, sample_c in out_dic.items():
        if int(sample_id) not in [3398, 3316, 3471, 3482, 3492, 3532, 3588, 3629, 3648, 3613, 3721, 3720, 3763]:
            write_jsonl(new_path, [sample_c], append=True)
    # print(result)


if __name__ == "__main__":
    main(n_workers=config['translation']['n_workers'], retry_cnt=config['translation']['retry_cnt'], out_path=config['dataset']['output'])
    # check_correctness()
    # fall_back()
    # check_leak()
    # remove_error()
    # remove_spec()