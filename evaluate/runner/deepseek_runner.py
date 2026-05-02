import os
import time
from time import sleep

try:
    import openai
    from openai import OpenAI
except ImportError as e:
    pass

from evaluate.runner.base_runner import BaseRunner


class DeepSeekRunner(BaseRunner):
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY", os.getenv("DOUBAO_API_KEY")),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    )

    def __init__(self, args, model, gen_num):
        super().__init__(args, model)
        # Endpoint IDs are provisioned per account in the Volcengine Ark console.
        self.DEEPSEEK_END_POINT_V3 = os.getenv("DEEPSEEK_ENDPOINT_V3", "")
        self.DEEPSEEK_END_POINT_R1 = os.getenv("DEEPSEEK_ENDPOINT_R1", "")
        self.client_kwargs: dict[str | str] = {
            # "model": args.model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "top_p": args.top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "n": 1,
            "timeout": 130,
            # "stop": args.stop, --> stop is only used for base models currently
        }
        self.gen_num = gen_num

    def _run_one(self, prompt: tuple[str, list[dict[str, str]]]) -> str:
        """Run a single API call with retries. Returns the generated string or '' on failure."""
        assert isinstance(prompt[1], list)

        def __run_single_stream():
            try:
                time.sleep(1)
                response = self.client.chat.completions.create(
                    model=self.DEEPSEEK_END_POINT_V3,
                    messages=prompt[1],
                    stream=True,
                    **self.client_kwargs,
                )

                content_parts = []
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        content_parts.append(delta)

                return "".join(content_parts)

            except (
                    openai.APIError,
                    openai.RateLimitError,
                    openai.InternalServerError,
                    openai.OpenAIError,
                    openai.APIStatusError,
                    openai.APITimeoutError,
                    openai.APIConnectionError,
            ) as e:
                print("[__run_single_stream] Exception: ", repr(e))
                return None
            except Exception as e:
                print(f"[__run_single_stream] Failed to run the model for {prompt}!")
                print("Exception: ", repr(e))
                return None

        for attempt in range(15):
            result = __run_single_stream()
            if result is not None:
                return result
            time.sleep(1)
        return ""

    def _run_single(self, prompt: tuple[str, list[dict[str, str]]]) -> list[str]:
        """Legacy batch API: generate all n samples sequentially for one prompt."""
        default_n = getattr(self.args, "n", 10)
        gen_count = self.gen_num.get(str(prompt[0]), default_n)
        print(f'{prompt[0]} need to generate {gen_count} codes')
        outputs = []
        for i in range(gen_count):
            outputs.append(self._run_one(prompt))
        return outputs
