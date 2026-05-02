from datasets import load_dataset, Dataset
from trl import GRPOTrainer, GRPOConfig
import datasets
from cppcheck import compute_score, logger
import json
import torch


dataset = datasets.load_from_disk("/workspace/benchC/evaluate/raw_datasets/apps_train/dataset")

grpo_config = GRPOConfig(
    max_completion_length = 1024,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=1,
    gradient_checkpointing=False,
    num_generations=2,
    bf16=True,
    model_init_kwargs={
        "torch_dtype": torch.bfloat16,
        "device_map": "auto"
    }
)

# Dummy reward function: count the number of unique characters in the completions
def reward_func(prompts, completions, **kwargs):
    rewards = []
    # print(f"kwargs: {type(kwargs)}, {kwargs}")
    input_outputs = kwargs.get("input_output", [None] * len(prompts)) 
    for i, (prompt, completion) in enumerate(zip(prompts, completions)):
        if isinstance(completion, list):
            completion = next((item['content'] for item in completion if item['role'] == 'assistant'), "")

        extra_info_raw = input_outputs[i]  # 取第 i 个样本对应的额外字段（字符串）
        extra_info_parsed = json.loads(extra_info_raw) if extra_info_raw is not None else {}
        extra_info = {"input_output": extra_info_parsed}  # 转成你需要的字典格式
        logger.info(f"[comp]:\n {completion}")
        reward = compute_score(
            data_source=prompt,
            solution_str=completion,
            ground_truth=None,
            extra_info=extra_info
        )
        rewards.append(reward)
    return rewards

trainer = GRPOTrainer(
    model="/workspace/models/Qwen2.5-Coder-7B-Instruct-bf16/",  # 本地模型路径
    args=grpo_config,
    reward_funcs=reward_func,
    train_dataset=dataset,
)
trainer.train()