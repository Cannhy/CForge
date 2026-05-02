import json
import os

from typing import Any
from evaluate.benchmarks.constant import ProblemType

try:
    from anthropic import HUMAN_PROMPT, AI_PROMPT
except ImportError:
    HUMAN_PROMPT = None
    AI_PROMPT = None

from evaluate.llm_styles import LMStyle
from evaluate.benchmarks.hard import HardProblem
from evaluate.benchmarks.introductory import IntroductoryProblem
from evaluate.benchmarks.easy import EasyProblem
from evaluate.benchmarks.medium import MediumProblem


class PromptConstants:
    SYSTEM_MESSAGE_GENERIC = f"You are an expert C programmer. You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests."

    SYSTEM_MESSAGE_GEMINI = f"You are an expert C programmer. You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests. Do NOT use system calls like `exit` in the generated program. Ensure that the first code block contains the solution."

    SYSTEM_MESSAGE_GEMINITHINK = f"You are an expert C programmer. You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests."

    SYSTEM_MESSAGE_DEEPSEEK = f"You are an AI programming assistant, utilizing the DeepSeek Coder model, developed by DeepSeek Company, and you answer questions related to computer science."

    SYSTEM_MESSAGE_CODEQWEN = (
        f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user"
    )

    SYSTEM_MESSAGE_QWEN_QWQ = f"<|im_start|>system\nYou are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step.<|im_end|>\n<|im_start|>user"

    SYSTEM_MESSAGE_DEEPSEEK_R1 = (
        "<｜begin▁of▁sentence｜>A conversation between User and Assistant. "
        "The user asks a question, and the Assistant solves it. "
        "The assistant first thinks about the reasoning process in the mind and then provides the user with the answer. "
        "The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>.<｜User｜>"
    )

    FORMATTING_MESSAGE_WITH_STARTER_CODE = "You will implement the following C starter code to write the solution to the problem. Mention that you can define some struct or functions before the starter code."

    FORMATTING_WITHOUT_STARTER_CODE = "Read the inputs from stdin solve the problem and write the answer to stdout (do not directly test on the sample inputs). Ensure that when the C program runs, it reads the inputs, runs the algorithm and writes output to STDOUT."


def get_generic_question_template_answer(question: IntroductoryProblem | EasyProblem | MediumProblem | HardProblem):
    prompt = f"### Question:\n{question.question_content}\n\n"
    if question.type == ProblemType.CALL_BASED or question.type == ProblemType.CALL_BASED_CTYPES:
        prompt += (
            f"### Format: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        )
        prompt += f"```C\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"### Format: {PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += "```C\n# YOUR CODE HERE\n```\n\n"
    prompt += f"### Answer: (use the provided format with backticks)\n\n"
    return prompt


def get_oaireason_question_template_answer(question: HardProblem):
    prompt = f"### Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += (
            f"### Format: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        )
        prompt += f"```C\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"### Format: Implement a function called `main()` which orchastrates the solution by reading inputs from stdin and writing the answer to stdout. Feel free to use additional functions as necessary. Next do NOT forget to call `main` function at the end of the program otherwise you will not be awarded any points.\n"
        prompt += "```C\n# YOUR CODE HERE\n```\n\n"
    prompt += f"### Answer: (use the provided format with backticks)\n\n"
    return prompt


def get_geminithinking_question_template_answer(question: HardProblem):
    prompt = f"### Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += (
            f"### Format: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        )
        prompt += f"```C\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"### Format: {PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += "```C\n# YOUR CODE HERE\n```\n\n"
    prompt += f"### Answer: (use the provided format with backticks)\n\n"
    return prompt


def get_deepseekcode_question_template_answer(question: HardProblem):
    prompt = f"### Instruction: You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests. You will NOT return anything except for the program.\n\n"
    prompt += f"Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += (
            f"### Instruction: {PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        )
        prompt += f"```C\n{question.starter_code}\n```\n\n"
    else:
        prompt += (
            f"### Instruction: {PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        )
        prompt += f"```C\n# YOUR CODE HERE\n```\n\n"
    prompt += f"### Response:\n\n"
    return prompt


def get_qwen_question_template_answer(question: HardProblem):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "/abacus/models/Qwen1.5-72B-Chat/", padding_side="left", use_fast=False
    )
    prompt = "You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests. You will NOT return anything except for the program.\n\n"
    prompt += f"Question:\n{question.question_content}\n\n"
    if question.starter_code:
        prompt += f"{PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        prompt += f"```C\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"{PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n\n"
        prompt += f"```C\n# YOUR CODE HERE\n```\n\n"

    messages = [
        {"role": "system", "content": PromptConstants.SYSTEM_MESSAGE_GENERIC},
        {"role": "user", "content": prompt},
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        truncation=False,
        padding=False,
    )
    return prompt


def get_codeqwen_question_template_answer(question: HardProblem):
    prompt = "You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests. You will NOT return anything except for the program.\n\n"
    prompt += f"Question: {question.question_content}\n\n"
    if question.starter_code:
        prompt += f"{PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        prompt += f"```C\n{question.starter_code}\n```\n\n<|im_end|>\n"
    else:
        prompt += f"{PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += f"```C\n# YOUR CODE HERE\n```\n\n<|im_end|>\n"
    prompt += f"<|im_start|>assistant\n"
    return prompt


def get_qwen_qwq_question_template_answer(question: HardProblem):
    prompt = "You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests.\n\n"
    prompt += f"Question: {question.question_content}\n\n"
    if question.starter_code:
        prompt += f"{PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        prompt += f"```C\n{question.starter_code}\n```\n\n<|im_end|>\n"
    else:
        prompt += f"{PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += f"```C\n# YOUR CODE HERE\n```\n\n<|im_end|>\n"
    prompt += f"<|im_start|>assistant\n"
    return prompt



def get_deepseek_r1_question_template_answer(question: IntroductoryProblem | EasyProblem | MediumProblem | HardProblem):
    # Following modifications from: https://github.com/fanqiwan/FuseAI/blob/main/FuseO1-Preview/code_evaluation/lcb_runner_cq/prompts/code_generation.py
    prompt = "<｜begin▁of▁sentence｜>\n<｜User｜>You will be given a question (problem specification) and will generate a correct C program that matches the specification and passes all tests.\n\n"
    prompt += f"Question: {question.question_content}\n\n"
    if question.type == ProblemType.CALL_BASED or question.type == ProblemType.CALL_BASED_CTYPES:
        prompt += f"{PromptConstants.FORMATTING_MESSAGE_WITH_STARTER_CODE}\n"
        if question.starter_code == "":
            txt = question.question_content
            st_code = txt.split("*/", 1)[-1].strip()
            prompt += f"```C\n{st_code}\n```\n\n"
        else:
            prompt += f"```C\n{question.starter_code}\n```\n\n"
    else:
        prompt += f"{PromptConstants.FORMATTING_WITHOUT_STARTER_CODE}\n"
        prompt += f"```C\n# YOUR CODE HERE\n```\n\n"
    prompt += "Write your reasoning **only inside <think>...</think>, using one sentence**. No extra text outside <think> tags. Then generate the complete C code inside ```c ...```. The reasoning must be minimal and precise."
    prompt += f"<｜Assistant｜>"
    return prompt


with open("evaluate/prompts/few_shot_examples/generation/func.json") as f:
    func = json.load(f)

with open("evaluate/prompts/few_shot_examples/generation/stdin.json") as f:
    stdin = json.load(f)


def get_base_model_question_template_answer(question: HardProblem):
    if question.starter_code:
        examples_json = func
    else:
        examples_json = stdin

    def get_example_prompt(example):
        prompt = ""
        prompt += "### Question\n"
        prompt += example["question"]
        prompt += "\n\n"
        if question.starter_code:
            prompt += "### Starter Code\n"
            prompt += example["sample_code"]
            prompt += "\n\n"
        prompt += "### Answer\n\n"
        prompt += example["answer"]
        if example["answer"]:
            prompt += "\n\n"
        return prompt

    prompt = ""
    prompt += get_example_prompt(examples_json[0])
    prompt += get_example_prompt(
        {
            "question": question.question_content,
            "sample_code": question.starter_code,
            "answer": "",
        }
    )
    return prompt


def format_prompt_generation(
    question: IntroductoryProblem | EasyProblem | MediumProblem | HardProblem, LanguageModelStyle: LMStyle, n_shot: int
) -> str | list[dict[str, str] | dict[str, str]] | list[dict[str, str]] | list[dict[str, str]] | list[dict[str, str]] | \
     tuple[str, list[dict[str, str]]] | Any:
    if LanguageModelStyle in [
        LMStyle.OpenAIChat,
        LMStyle.DeepSeekAPI,
        LMStyle.TogetherAI,
        LMStyle.CohereCommand,
        LMStyle.DoubaoAPI,
        LMStyle.LubanAPI,
        LMStyle.VllmAI
    ]:
        chat_messages = [
            {
                "role": "system",
                "content": PromptConstants.SYSTEM_MESSAGE_GENERIC,
            },
        ]
        user_content = ""

        # if True:
        if question.type == ProblemType.IO_BASED:
            few_shots_path = os.path.join(
                os.path.dirname(__file__), "few_shot_examples", "generation",
                "stdin.json"
            )
        else:
            few_shots_path = os.path.join(
                os.path.dirname(__file__), "few_shot_examples", "generation",
                "func.json"
            )

        with open(few_shots_path, "r", encoding="utf-8") as f:
            few_shots = json.load(f)
        i = 0
        for shot in few_shots:
            if i >= n_shot:
                break
            user_content += "### Question:\n" + shot["question"] + "\n"
            if shot.get("sample_code"):
                user_content += "### Starter_code:\n" + shot["sample_code"] + "\n"
            user_content += "### Code:\n" + shot["answer"] + "\n\n"

        # 当前问题
        if n_shot > 0:
            user_content += "The above examples are reference code snippets. Please do not repeat them, just use them as guidance.\n\n" + get_generic_question_template_answer(question) + "\n"
        else:
            user_content += get_generic_question_template_answer(question) + "\n"

        chat_messages.append({
            "role": "user",
            "content": user_content,
        })
        return question.question_id, chat_messages
    elif LanguageModelStyle in [LMStyle.OpenAIReasonPreview, LMStyle.Grok]:
        chat_messages = [
            {
                "role": "user",
                "content": PromptConstants.SYSTEM_MESSAGE_GENERIC
                + "\n\n"
                + get_generic_question_template_answer(question),
            },
        ]
        return chat_messages
    elif LanguageModelStyle == LMStyle.OpenAIReason:
        chat_messages = [
            {
                "role": "user",
                "content": PromptConstants.SYSTEM_MESSAGE_GENERIC
                + "\n\n"
                + get_oaireason_question_template_answer(question),
            },
        ]
        return chat_messages

    if LanguageModelStyle == LMStyle.LLaMa3:
        chat_messages = [
            {
                "role": "system",
                "content": PromptConstants.SYSTEM_MESSAGE_GENERIC,
            },
        ]
        chat_messages += [
            {
                "role": "user",
                "content": get_generic_question_template_answer(question),
            },
        ]
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Meta-Llama-3-8B-Instruct", padding_side="left", use_fast=False
        )
        return tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True,
            truncation=False,
            padding=False,
        )

    if LanguageModelStyle == LMStyle.Claude:
        prompt = f"{HUMAN_PROMPT}\n"
        prompt += f"{PromptConstants.SYSTEM_MESSAGE_GENERIC}\n\n"
        prompt += f"{get_generic_question_template_answer(question).rstrip()}\n"
        prompt += f"{AI_PROMPT}"
        return prompt

    if LanguageModelStyle in [LMStyle.Claude3, LMStyle.Claude3Thinking]:
        system = PromptConstants.SYSTEM_MESSAGE_GENERIC
        prompt = [
            {
                "role": "user",
                "content": get_generic_question_template_answer(question).rstrip(),
            }
        ]
        return system, prompt

    if LanguageModelStyle == LMStyle.Gemini:
        prompt = f"{PromptConstants.SYSTEM_MESSAGE_GEMINI}\n"
        prompt += f"{get_generic_question_template_answer(question)}"
        return prompt

    if LanguageModelStyle == LMStyle.GeminiThinking:
        prompt = f"{PromptConstants.SYSTEM_MESSAGE_GEMINITHINK}\n"
        prompt += f"{get_geminithinking_question_template_answer(question)}"
        return prompt

    if LanguageModelStyle == LMStyle.MistralWeb:
        chat_messages = [
            {
                "role": "system",
                "content": PromptConstants.SYSTEM_MESSAGE_GENERIC,
            },
            {
                "role": "user",
                "content": get_generic_question_template_answer(question),
            },
        ]
        return chat_messages

    if LanguageModelStyle == LMStyle.DeepSeekCodeInstruct:
        prompt = f"{PromptConstants.SYSTEM_MESSAGE_DEEPSEEK}\n\n"
        prompt += f"{get_deepseekcode_question_template_answer(question)}"
        return prompt

    if LanguageModelStyle == LMStyle.CodeQwenInstruct:
        prompt = f"{PromptConstants.SYSTEM_MESSAGE_CODEQWEN}\n\n"
        prompt += f"{get_codeqwen_question_template_answer(question)}"
        return prompt

    if LanguageModelStyle == LMStyle.QwQ:
        prompt = f"{PromptConstants.SYSTEM_MESSAGE_QWEN_QWQ}\n\n"
        prompt += f"{get_qwen_qwq_question_template_answer(question)}"
        return prompt

    if LanguageModelStyle == LMStyle.DeepSeekR1:
        prompt = f"{PromptConstants.SYSTEM_MESSAGE_DEEPSEEK_R1}"
        prompt += f"{get_deepseek_r1_question_template_answer(question)}"
        return prompt

    if LanguageModelStyle == LMStyle.GenericBase:
        prompt = get_base_model_question_template_answer(question)
        return prompt

    raise NotImplementedError(
        f"LanguageModelStyle {LanguageModelStyle} not implemented"
    )


def test():
    import pathlib

    base_dir = "logs/example_prompts/generation"
    pathlib.Path(base_dir).mkdir(parents=True, exist_ok=True)

    for lmstyle in LMStyle:
        generation_problem = IntroductoryProblem(
            question_content="question-content",
            question_id="question_id",
            starter_code="",
            test_code="",
            solution="",
            type="call_based",
        )
        prompt1 = format_prompt_generation(generation_problem, lmstyle, n_shot=0)
        with open(f"{base_dir}/{lmstyle}_1.txt", "w") as f:
            try:
                f.write(prompt1)
            except TypeError:
                f.write(json.dumps(prompt1))

        generation_problem.starter_code = "starter code"
        prompt2 = format_prompt_generation(generation_problem, lmstyle, n_shot=0)
        with open(f"{base_dir}/{lmstyle}_2.txt", "w") as f:
            try:
                f.write(prompt2)
            except TypeError:
                f.write(json.dumps(prompt2))


if __name__ == "__main__":
    test()
