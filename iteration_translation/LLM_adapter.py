import time

from openai import OpenAI
from zhipuai import ZhipuAI
from google import genai


class LLMAdapter:
    def __init__(self):
        self.DOUBAO_KEY = ""
        self.DOUBAO_BASE_URL = ""
        self.DOUBAO_END_POINT_32K = ""
        self.DOUBAO_END_POINT_256K = ""
        self.DOUBAO_DS_POINT = ""

        self.KIMI_KEY = ""
        self.KIMI_BASE_URL = "https://api.moonshot.cn/v1"

        self.QWEN_KEY = ""
        self.QWEN_BASE_URL = ""

        self.DEEPSEEK_API_KEY = ""
        self.DEEPSEEK_BASE_URL = "https://api.deepseek.com"

        self.GEMENI_API_KEY = ""

        self.ZHIPU_API_KEY = ""

        self.doubao_client = OpenAI(api_key=self.DOUBAO_KEY, base_url=self.DOUBAO_BASE_URL)
        self.kimi_client = OpenAI(api_key=self.KIMI_KEY, base_url=self.KIMI_BASE_URL)
        self.deepseek_client = OpenAI(api_key=self.DEEPSEEK_API_KEY, base_url=self.DEEPSEEK_BASE_URL)
        self.zhipu_client = ZhipuAI(api_key=self.ZHIPU_API_KEY)
        self.qwen_client = OpenAI(api_key=self.QWEN_KEY, base_url=self.QWEN_BASE_URL)
        self.gemini_client = genai.Client(api_key=self.GEMENI_API_KEY)

        self.system_prompt = "You are an expert in translating Python code to C code, including prompts, function signatures, implementations, and test cases. Follow formatting strictly and reason carefully when fixing errors."

    def completion(self, ai_cop, model_name, prompt):
        global compl_resp
        time.sleep(3)
        if ai_cop == 'qwen':
            compl_resp = self.qwen_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": self.system_prompt},
                    {"role": "user",
                     "content": prompt},
                ],
            )
        elif ai_cop == 'zhipu':
            compl_resp = self.zhipu_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": self.system_prompt},
                    {"role": "user",
                     "content": prompt},
                ],
            )
        elif ai_cop == 'kimi':
            compl_resp = self.kimi_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": self.system_prompt},
                    {"role": "user",
                     "content": prompt},
                ],
                temperature=0.3,
            )
        elif ai_cop == 'doubao':
            compl_resp = self.doubao_client.chat.completions.create(
                model=self.DOUBAO_END_POINT_256K,
                messages=[
                    {"role": "system",
                     "content": self.system_prompt},
                    {"role": "user",
                     "content": prompt},
                ],
            )
        resp = compl_resp.choices[0].message.content
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(resp)
        return resp