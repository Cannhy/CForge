import os
import time
from time import sleep

try:
    import openai
    from openai import OpenAI
except ImportError as e:
    pass

from evaluate.runner.base_runner import BaseRunner


class DoubaoRunner(BaseRunner):
    client = OpenAI(
        api_key=os.getenv("DOUBAO_API_KEY"),
        base_url=os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    )

    def __init__(self, args, model):
        super().__init__(args, model)
        # Endpoint IDs are provisioned per account in the Volcengine Ark console.
        # Override via environment variables.
        self.DOUBAO_END_POINT_32K = os.getenv("DOUBAO_ENDPOINT_32K", "")
        self.DOUBAO_END_POINT_256K = os.getenv("DOUBAO_ENDPOINT_256K", "")
        self.client_kwargs: dict[str | str] = {
            # "model": args.model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "top_p": args.top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "n": 1,
            "timeout": args.openai_timeout,
            # "stop": args.stop, --> stop is only used for base models currently
        }

    def _run_single(self, prompt: list[dict[str, str]]) -> list[str]:
        assert isinstance(prompt, list)

        def __run_single(counter):
            try:
                time.sleep(2)
                response = self.client.chat.completions.create(
                    model=self.DOUBAO_END_POINT_256K,
                    messages=prompt,
                    **self.client_kwargs,
                )
                content = response.choices[0].message.content
                return content
            except (
                openai.APIError,
                openai.RateLimitError,
                openai.InternalServerError,
                openai.OpenAIError,
                openai.APIStatusError,
                openai.APITimeoutError,
                openai.InternalServerError,
                openai.APIConnectionError,
            ) as e:
                print("Exception: ", repr(e))
                print("Sleeping for 30 seconds...")
                print("Consider reducing the number of parallel processes.")
                sleep(30)
                return DoubaoRunner._run_single(prompt)
            except Exception as e:
                print(f"Failed to run the model for {prompt}!")
                print("Exception: ", repr(e))
                raise e

        outputs = []
        try:
            for _ in range(self.args.n):
                outputs.append(__run_single(10))
        except Exception as e:
            raise e
        return outputs
