import os
import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from tqdm import tqdm
from evaluate.utils.path_utils import get_cache_path
from evaluate.llm_styles import LanguageModel
from evaluate.utils.multiprocess import (
    run_tasks_in_parallel,
    run_tasks_in_parallel_iter,
)


class BaseRunner(ABC):
    def __init__(self, args, model: LanguageModel):
        self.args = args
        self.model = model
        self.client_kwargs: dict[str | str] = {}

        if self.args.use_cache:
            self.cache_path = get_cache_path(model.model_repr, args)
            if os.path.exists(self.cache_path):
                with open(self.cache_path) as f:
                    self.cache: dict = json.load(f)
            else:
                self.cache = {}
        else:
            self.cache_path = None
            self.cache = None

    def save_cache(self):
        if self.args.use_cache:
            with open(self.cache_path, "w") as f:
                json.dump(self.cache, f, indent=4)

    # @abstractmethod
    def _run_single(self, prompt: tuple[str, list[dict[str, str]]]) -> list[str]:
        pass

    @staticmethod
    def run_single(combined_args) -> list[str]:
        """
        Run the model for a single prompt and return the output
        Static method to be used in multiprocessing
        Calls the _run_single method with the combined arguments
        """
        prompt: str | tuple[str, list[dict[str, str]]]
        cache: dict[str, str]
        call_method: callable
        prompt, cache, args, call_method = combined_args

        if isinstance(prompt, list):
            prompt_cache = json.dumps(prompt)
        elif isinstance(prompt, tuple):
            prompt_cache = str(prompt[0]) + json.dumps(prompt[1])
        else:
            prompt_cache = prompt

        if cache is not None and prompt_cache in cache:
            if len(cache[prompt_cache]) == args.n:
                return cache[prompt_cache]

        result = call_method(prompt)

        return result

    def run_batch(self, prompts: list[str | list[dict[str, str]]] | list[tuple[str, list[dict[str, str]]]]) -> list[list[str]]:
        outputs = []
        arguments = [
            (
                prompt,
                self.cache,  ## pass the cache as argument for cache check
                self.args,  ## pass the args as argument for cache check
                self._run_single,  ## pass the _run_single method as argument because of multiprocessing
            )
            for prompt in prompts
        ]
        if self.args.multiprocess > 1:
            parallel_outputs = run_tasks_in_parallel(
                self.run_single,
                arguments,
                self.args.multiprocess,
                use_progress_bar=True,
            )
            for output in parallel_outputs:
                if output.is_success():
                    outputs.append(output.result)
                else:
                    print("Failed to run the model for some prompts")
                    print(output.status)
                    print(output.exception_tb)
                    outputs.extend([""] * self.args.n)
        else:
            outputs = [self.run_single(argument) for argument in tqdm(arguments)]

        if self.args.use_cache:
            for prompt, output in zip(prompts, outputs):
                if isinstance(prompt, list):
                    prompt_cache = json.dumps(prompt)
                elif isinstance(prompt, tuple):
                    prompt_cache = str(prompt[0]) + json.dumps(prompt[1])
                else:
                    prompt_cache = prompt
                self.cache[prompt_cache] = output  ## save the output to cache

        return outputs

    def prompts_to_outputs(
        self, prompts: list[str | list[dict[str, str]]] | list[tuple[str, list[dict[str, str]]]]
    ) -> list[list[str]]:
        if self.args.use_cache:
            outputs = []
            batch_size = self.args.cache_batch_size
            for i in range(0, len(prompts), batch_size):
                batch = prompts[i : i + batch_size]
                batch_outputs = self.run_batch(batch)
                outputs.extend(batch_outputs)
                self.save_cache()
        else:
            outputs = self.run_batch(prompts)
        return outputs

    def run_main(self, benchmark: list, format_prompt: callable) -> list[list[str]]:

        prompts = [
            format_prompt(problem, self.model.model_style) for problem in benchmark
        ]
        outputs = self.prompts_to_outputs(prompts)
        return outputs

    def run_main_stream(
        self,
        benchmark: list,
        format_prompt: Callable,
        on_result: Optional[Callable[[int, "object", list[str]], None]] = None,
    ) -> list[list[str]]:
        """
        Streaming variant of `run_main`: as soon as a single prompt is finished
        by any worker, the main process invokes `on_result(index, problem, outputs_list)`
        so the caller can persist the result to disk immediately.

        - `index` is the position of the problem in `benchmark` (stable ordering).
        - `problem` is the original benchmark item (for metadata like question_id).
        - `outputs_list` is the list of raw generations for this prompt.

        Returns the full outputs list in the original `benchmark` order so that
        downstream code (combine_results / evaluation) keeps working unchanged.
        """
        prompts = [
            format_prompt(problem, self.model.model_style) for problem in benchmark
        ]

        # Pack (index, prompt) into the task payload so we can route results
        # back to the correct benchmark item as tasks complete out of order.
        indexed_arguments = [
            (
                idx,
                (
                    prompt,
                    self.cache,
                    self.args,
                    self._run_single,
                ),
            )
            for idx, prompt in enumerate(prompts)
        ]

        outputs: list[list[str]] = [[] for _ in prompts]

        if self.args.multiprocess > 1:
            iterator = run_tasks_in_parallel_iter(
                _run_single_with_index,
                indexed_arguments,
                num_workers=self.args.multiprocess,
                use_progress_bar=True,
                progress_bar_desc="generation",
            )
            for task_result in iterator:
                if not task_result.is_success():
                    print("Failed to run the model for some prompt")
                    print(task_result.status)
                    print(task_result.exception_tb)
                    continue
                idx, result = task_result.result
                outputs[idx] = result
                if on_result is not None:
                    try:
                        on_result(idx, benchmark[idx], result)
                    except Exception as e:
                        # Never let a persistence error kill the worker loop.
                        print(f"[run_main_stream] on_result callback failed for idx={idx}: {e!r}")
        else:
            for idx, argument in enumerate(tqdm(indexed_arguments)):
                _, result = _run_single_with_index(argument)
                outputs[idx] = result
                if on_result is not None:
                    try:
                        on_result(idx, benchmark[idx], result)
                    except Exception as e:
                        print(f"[run_main_stream] on_result callback failed for idx={idx}: {e!r}")

        if self.args.use_cache:
            for prompt, output in zip(prompts, outputs):
                if isinstance(prompt, list):
                    prompt_cache = json.dumps(prompt)
                elif isinstance(prompt, tuple):
                    prompt_cache = str(prompt[0]) + json.dumps(prompt[1])
                else:
                    prompt_cache = prompt
                self.cache[prompt_cache] = output
            self.save_cache()

        return outputs

    def run_main_per_sample(
        self,
        benchmark: list,
        format_prompt: Callable,
        on_sample: Optional[Callable[["object", str], None]] = None,
    ) -> list[list[str]]:
        """
        Fine-grained streaming: each API call (one of the n samples for one
        problem) is a separate task submitted to a ThreadPool. Every time a
        single sample returns, the main thread invokes
        `on_sample(problem, raw_output_str)` so the caller can immediately
        append-and-flush to disk.

        This is the preferred path for pure-IO API runners (Luban, DeepSeek,
        ...) where _run_one is defined. If _run_one is missing, falls back to
        the batched run_main_stream path.
        """
        if not hasattr(self, "_run_one"):
            # Fallback: batched per-problem (old behaviour)
            def _batched_cb(idx, problem, outputs_list):
                if on_sample is None:
                    return
                for o in outputs_list:
                    on_sample(problem, o)

            return self.run_main_stream(
                benchmark=benchmark,
                format_prompt=format_prompt,
                on_result=_batched_cb,
            )

        # Build task list: (problem, prompt, sample_idx) — one task per sample
        default_n = getattr(self.args, "n", 10)
        gen_num: dict = getattr(self, "gen_num", {}) or {}

        tasks = []
        for problem in benchmark:
            prompt = format_prompt(problem, self.model.model_style)
            n_for_this = gen_num.get(str(problem.question_id), default_n)
            for sample_idx in range(n_for_this):
                tasks.append((problem, prompt, sample_idx))

        # Preserve per-problem ordering in the returned list (by problem pos)
        problem_pos = {id(p): i for i, p in enumerate(benchmark)}
        outputs_per_problem: list[list[str]] = [[] for _ in benchmark]

        max_workers = max(1, int(getattr(self.args, "multiprocess", 1)))

        def _worker(task):
            problem, prompt, sample_idx = task
            try:
                text = self._run_one(prompt)
            except Exception as e:
                print(f"[run_main_per_sample] _run_one failed for qid={problem.question_id}: {e!r}")
                text = ""
            return problem, sample_idx, text

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_worker, t) for t in tasks]
            pbar = tqdm(total=len(futures), desc="per-sample gen", dynamic_ncols=True)
            for fut in as_completed(futures):
                try:
                    problem, sample_idx, text = fut.result()
                except Exception as e:
                    print(f"[run_main_per_sample] future failed: {e!r}")
                    pbar.update(1)
                    continue
                outputs_per_problem[problem_pos[id(problem)]].append(text)
                if on_sample is not None:
                    try:
                        on_sample(problem, text)
                    except Exception as e:
                        print(f"[run_main_per_sample] on_sample callback failed: {e!r}")
                pbar.update(1)
            pbar.close()

        return outputs_per_problem


def _run_single_with_index(indexed_args):
    """
    Top-level helper (picklable) used by `run_main_stream` so that each worker
    returns `(index, result)` allowing out-of-order completion to be routed back.
    """
    idx, combined_args = indexed_args
    result = BaseRunner.run_single(combined_args)
    return idx, result
