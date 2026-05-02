import json
import time

import yaml
import logging

from datasets import load_from_disk
from datetime import datetime
from typing import List, Optional
from iteration_translation.sandbox.sandbox import *
from collections import defaultdict
from threading import Lock
from few_shots import translate_all_shots, translate_apps_call_based_shots
from tqdm.auto import tqdm
from template import translate_all_template, translate_apps_template
from LLM_adapter import LLMAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from process_human_eval import write_jsonl, read_problems

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    def __init__(self, task_id, py_prompt, py_sig="", py_code="", py_test=""):
        self.task_id = task_id
        self.py_prompt = py_prompt
        self.py_signature = py_sig
        self.py_code = py_code
        self.py_testcase = py_test

        self.c_prompt = ""
        self.c_signature = ""
        self.c_code = ""
        self.c_testcase = ""

        self.retry_cnt = -1
        self.final_result = "failed"

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "c_prompt": self.c_prompt,
            "c_signature": self.c_signature,
            "c_code": self.c_code,
            "c_testcase": self.c_testcase,
            "retry_cnt": self.retry_cnt,
            "final_result": self.final_result
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


def check_duplicate_ids():
    dataset_path = config['dataset']['output']
    dataset_dict = read_problems(dataset_path)

    counter = defaultdict(int)
    for sample in dataset_dict.values():
        counter[sample['task_id']] += 1

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
    previous_c_test: Optional[str] = None,
    run_feedback: Optional[str] = None
) -> str:
    return translate_apps_template.render(
        k=len(few_shot_examples),
        examples=few_shot_examples,
        target_python_prompt=sample.py_prompt,
        target_python_signature=sample.py_signature,
        target_python_code=sample.py_code,
        target_python_test=sample.py_testcase,
        previous_c_code=previous_c_code,
        previous_c_test=previous_c_test,
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



def format_run_result_as_feedback(run_result: Dict[str, Dict[str, str]]) -> str:
    feedback = ""
    compile_result = run_result["compile_result"]
    exec_result = run_result["execute_result"]

    if compile_result["return_code"] != "0":
        feedback += "Compilation failed:\n"
        feedback += compile_result["stderr"] or compile_result["stdout"]
    elif exec_result["return_code"] != "0":
        feedback += "Execution failed:\n"
        if exec_result["return_code"] == "timeout":
            feedback += "Timed out during execution."
        else:
            feedback += exec_result["stderr"] or exec_result["stdout"]
    else:
        feedback += "Execution successful."

    return feedback.strip()


def sample_to_dict(sample: Sample) -> Dict:
    return {
        "task_id": sample.task_id,
        "c_prompt": sample.c_prompt,
        "c_signature": sample.c_signature,
        "c_code": sample.c_code,
        "c_testcase": sample.c_testcase,
    }


def process_sample(sample: Sample,
                   few_shot_examples: List[Dict],
                   retry_cnt: int = 10,
                   output_path: str = "./mbpp/mbpp_c.jsonl"
                   ):
    try:
        prompt = build_prompt(sample, few_shot_examples)
        #logging.info(f'[task_id]: {sample.task_id}, [prompt 0]: {prompt}')
        #time.sleep(1000)
        model_output = llm.completion(ai_cop=ai_cop, model_name=model_name, prompt=prompt)
        logging.info(f'[task_id]: {sample.task_id}, [generation 0]:\n {model_output}')
        generated_prompt = extract_between_tags(model_output, "prompt", "signature")
        generated_signature = extract_between_tags(model_output, "signature", "code")
        generated_code = extract_between_tags(model_output, "code", "test_case")
        generated_test = extract_between_tags(model_output, "test_case")
        # print(f"[task_id: {sample.task_id}] Extracted Prompt:\n{generated_prompt}")
        # print(f"[task_id: {sample.task_id}] Extracted Signature:\n{generated_signature}")
        # print(f"[task_id: {sample.task_id}] Extracted Code:\n{generated_code}")
        # print(f"[task_id: {sample.task_id}] Extracted Test Case:\n{generated_test}")
        #time.sleep(10000)
        merged = generated_code + "\n" + generated_test
        run_result = run_code_snip(merged)
        logging.info(f'[task_id]: {sample.task_id}, [run_result 0]:\n {run_result}')
        if run_result["compile_result"]["return_code"] == "0" and run_result["execute_result"]["return_code"] == "0":
            # sample.c_prompt = generated_prompt
            sample.c_signature = generated_signature
            sample.c_code = generated_code
            sample.c_testcase = generated_test
            sample.retry_cnt = 0
            sample.final_result = "success"
            with write_lock:
                write_jsonl(config['dataset']['output'], [sample.to_dict()], append=True)
            return sample

        for i in range(retry_cnt):
            feedback = format_run_result_as_feedback(run_result)
            prompt = build_prompt(
                sample,
                few_shot_examples,
                previous_c_code=generated_code,
                previous_c_test=generated_test,
                run_feedback=feedback
            )
            #logging.info(f'[task_id]: {sample.task_id}, [prompt {i+1}]: {prompt}')
            model_output = llm.completion(ai_cop=ai_cop, model_name=model_name, prompt=prompt)
            logging.info(f'[task_id]: {sample.task_id}, [generation {i+1}]:\n {model_output}')
            # generated_prompt = extract_between_tags(model_output, "prompt", "signature")
            generated_signature = extract_between_tags(model_output, "signature", "code")
            generated_code = extract_between_tags(model_output, "code", "test_case")
            generated_test = extract_between_tags(model_output, "test_case")
            merged = generated_code + "\n" + generated_test
            run_result = run_code_snip(merged)

            # sample.c_prompt = generated_prompt
            sample.c_signature = generated_signature
            sample.c_code = generated_code
            sample.c_testcase = generated_test
            sample.retry_cnt = i
            logging.info(f'[task_id]: {sample.task_id}, [run_result {i+1}]:\n {run_result}')
            if run_result["compile_result"]["return_code"] == "0" and run_result["execute_result"]["return_code"] == "0":
                sample.final_result = "success"
                break
        with write_lock:
            write_jsonl(output_path, [sample.to_dict()], append=True)
        return sample
    except Exception as e:
        print(f"Error: {e}")
        with write_lock:
            write_jsonl(config['dataset']['output'], [{
                "task_id": getattr(sample, "task_id", "unknown"),
                "error": str(e),
                "final_result": "error"
            }], append=True)
        return {
            "error": str(e),
            "passed": False
        }


def main(
        n_workers: int = 4,
        retry_cnt: int = 5,
):
    dataset_path = config['dataset']['src_path']
    # dataset_dict = read_problems(dataset_path)
    dataset_dict = load_from_disk(dataset_path)
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []
        # for sample in tqdm(dataset_dict.values()):
        for sample in tqdm(dataset_dict):
            tmp_code = sample["solutions"]
            codes = json.loads(tmp_code) if tmp_code != "" else [""]
            sample_obj = Sample(task_id=sample['problem_id'], py_prompt=sample['question'], py_code=codes[0], py_test="\n".join(sample['input_output']))
            sample_obj.c_prompt = sample['question']
            if 2639 <= int(sample_obj.task_id):
                if "fn_name" in sample['input_output']:
                    args = (sample_obj, translate_apps_call_based_shots, retry_cnt)
                    future = executor.submit(process_sample, *args)
                    futures.append(future)
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing samples"):
        try:
            result = future.result()
            print(result.to_dict())
        except Exception as e:
            print(f"Error processing a sample: {e}")
    print(f"All results written to {config['dataset']['output']}")


def fall_back():
    py_path = config['dataset']['path']
    py_dict = read_problems(py_path)
    dataset_path = config['dataset']['output']
    dataset_dict = read_problems(dataset_path)

    to_retry = []
    succeeded = []
    for sample_id, sample in dataset_dict.items():
        if sample.get("final_result") == "failed" and "worker" not in sample:
            to_retry.append((sample_id, sample))
        else:
            succeeded.append((sample_id, sample))
    print(f"Found {len(to_retry)} samples to retry.")

    # 按 task_id 排序成功样本并写入
    succeeded_sorted = sorted(succeeded, key=lambda x: x[1]['task_id'])
    for _, sample in succeeded_sorted:
        write_jsonl(config['dataset']['backup'], [sample], append=True)
    print(f"Found {len(to_retry)} samples to retry.")
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for sample_id, sample_c in to_retry:
            print(f"Retrying sample {sample_id}...")
            py_sample = py_dict[sample_id]
            sample_src = Sample(task_id=sample_c['task_id'], py_prompt=py_sample['text'], py_code=py_sample['code'],
                                py_test="\n".join(py_sample['test_list']))
            sample_src.c_code = sample_c['c_code']
            sample_src.c_testcase = sample_c['c_testcase']
            args = (sample_src, translate_all_shots, 10, config['dataset']['backup'])
            future = executor.submit(process_sample, *args)
            futures.append(future)
            time.sleep(10)
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing failed samples"):
        try:
            result = future.result()
            print(result.to_dict())
        except Exception as e:
            print(f"Error processing a sample: {e}")
    print(f"All results written to {config['dataset']['output']}")


def fall_back_specific():
    py_path = config['dataset']['path']
    py_dict = read_problems(py_path)

    to_retry = [64, 117, 118, 128, 143, 215, 294, 297, 298, 301, 314, 381, 396, 403, 413, 465, 484, 493]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for task_id in to_retry:
            print(f"Retrying sample {task_id}...")
            py_sample = py_dict[task_id]
            sample_src = Sample(task_id=task_id, py_prompt=py_sample['text'], py_code=py_sample['code'],
                                py_test="\n".join(py_sample['test_list']))
            args = (sample_src, translate_all_shots, 8, config['dataset']['retry'])
            future = executor.submit(process_sample, *args)
            futures.append(future)
            time.sleep(10)
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing retry samples"):
        try:
            result = future.result()
            print(result.to_dict())
        except Exception as e:
            print(f"Error processing a sample: {e}")
    print(f"All results written to {config['dataset']['output']}")


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

if __name__ == "__main__":
    main(n_workers=config['translation']['n_workers'], retry_cnt=config['translation']['retry_cnt'])
    # check_correctness()
    # fall_back()