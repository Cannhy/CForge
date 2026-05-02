import os
import random
import time
from time import sleep

try:
    import openai
    from openai import OpenAI
except ImportError as e:
    pass

from evaluate.runner.base_runner import BaseRunner

# All credentials/endpoints are loaded from environment variables so that no
# secrets are hard-coded in this file. See ``.env.example`` for the full list.
LUBAN_API_KEY = os.getenv("LUBAN_API_KEY", "EMPTY")
LUBAN_BASE_URL = os.getenv("LUBAN_BASE_URL", "")
LUBAN_REQUEST_UIN = os.getenv("LUBAN_REQUEST_UIN", "")
LUBAN_REQUEST_TOKEN = os.getenv("LUBAN_REQUEST_TOKEN", "")
LUBAN_REQUEST_BUSINESS = os.getenv("LUBAN_REQUEST_BUSINESS", "")
DEFAULT_MODEL_NAME = os.getenv("LUBAN_DEFAULT_MODEL", "")


def create_luban_client() -> OpenAI:
    if not LUBAN_BASE_URL:
        raise RuntimeError(
            "LUBAN_BASE_URL is not set. Please configure the Luban endpoint "
            "via environment variables (see .env.example)."
        )
    header = {
        "Luban-Request-Trace-ID": "ytk.{}.{}".format(
            random.randint(0, 999999), int(time.time() * 1000)),
        "Luban-Request-UIN": LUBAN_REQUEST_UIN,
        "Luban-Request-Token": LUBAN_REQUEST_TOKEN,
        "Luban-Request-Business": LUBAN_REQUEST_BUSINESS,
    }
    return OpenAI(
        api_key=LUBAN_API_KEY,
        base_url=LUBAN_BASE_URL,
        default_headers=header,
    )


class LubanRunner(BaseRunner):
    client = None  # lazily initialised so import does not fail when env vars missing

    def __init__(self, args, model, gen_num):
        super().__init__(args, model)
        if LubanRunner.client is None:
            LubanRunner.client = create_luban_client()
        self.model_name = args.luban_model_name or DEFAULT_MODEL_NAME
        self.client_kwargs: dict[str | str] = {
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "top_p": args.top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "n": 1,
            "timeout": 130,
        }
        self.gen_num = gen_num

    def _run_one(self, prompt: tuple[str, list[dict[str, str]]]) -> str:
        """Run a single API call with retries. Returns the generated string or '' on failure."""
        assert isinstance(prompt[1], list)

        def __run_single_call():
            try:
                time.sleep(1)
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=prompt[1],
                    **self.client_kwargs,
                )
                return response.choices[0].message.content
            except (
                openai.APIError,
                openai.RateLimitError,
                openai.InternalServerError,
                openai.OpenAIError,
                openai.APIStatusError,
                openai.APITimeoutError,
                openai.APIConnectionError,
            ) as e:
                print("[__run_single_call] Exception: ", repr(e))
                return None
            except Exception as e:
                print(f"[__run_single_call] Failed to run the model for {prompt}!")
                print("Exception: ", repr(e))
                return None

        for attempt in range(15):
            result = __run_single_call()
            if result is not None:
                return result
            time.sleep(2 ** attempt)
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
