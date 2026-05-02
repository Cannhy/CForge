from human_eval.data import write_jsonl, read_problems
import re

problemc_c = read_problems("E:\codeGen\exp\exp_docker\code_gen_self-plan\\benchmark\HumanEval\humaneval_c.jsonl")

for task_id in problemc_c:
    sample = problemc_c[task_id]
    prompt_old = sample['prompt']
    text_list = list(prompt_old)
    sz = len(text_list)
    cnt = 0
    for i in range(sz - 1, -1, -1):
        if text_list[i] == '{':
            # 找到第一个 '{' 替换为 ');'
            text_list[i] = ';'
            break  # 替换后退出循环
        cnt += 1
        if cnt >= 4: break
    prompt_new = ''.join(text_list)
    sample['prompt'] = prompt_new
    samples = [sample]
    write_jsonl("E:\codeGen\exp\exp_docker\code_gen_self-plan\\benchmark\HumanEval\humaneval_c.jsonl", samples, True)
