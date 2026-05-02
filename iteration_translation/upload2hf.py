"""
Helper script for pushing the curated CForge jsonl data to the HuggingFace
dataset repo. Also contains a small utility for pulling a local copy of a
reference model (kept here for reproducibility of the training setup).

Usage:
    # Upload the local CForge_data/ mirror to the HF dataset
    export HF_TOKEN=hf_xxx
    python iteration_translation/upload2hf.py --upload

    # Download a reference model for evaluation / training
    python iteration_translation/upload2hf.py --download-model \
        --model-name Qwen/Qwen2.5-Coder-7B-Instruct \
        --save-dir ../models/Qwen2.5-Coder-7B-Instruct-fp16
"""

import argparse
import os
import sys

sys.set_int_max_str_digits(100000)


def upload_cforge(local_dir: str, repo_id: str):
    from huggingface_hub import HfApi
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is not set")
    api = HfApi(token=token)
    api.upload_folder(
        folder_path=local_dir,
        repo_id=repo_id,
        repo_type="dataset",
    )
    print(f"Uploaded {local_dir} -> {repo_id}")


def download_model(model_name: str, save_dir: str, dtype: str = "float16"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch_dtype = {"float16": torch.float16, "bfloat16": torch.bfloat16,
                   "float32": torch.float32}[dtype]

    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch_dtype,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    os.makedirs(save_dir, exist_ok=True)
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)
    print(f"Saved {model_name} -> {save_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action="store_true",
                        help="Upload CForge_data/ to the HF dataset repo")
    parser.add_argument(
        "--local-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "CForge_data"),
        help="Local directory to upload",
    )
    parser.add_argument("--repo-id", default="cannhy/CForge",
                        help="HF dataset repo id")

    parser.add_argument("--download-model", action="store_true",
                        help="Download a HF model snapshot locally")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    parser.add_argument("--save-dir", default="../models/Qwen2.5-Coder-7B-Instruct-fp16")
    parser.add_argument("--dtype", default="float16",
                        choices=["float16", "bfloat16", "float32"])

    args = parser.parse_args()

    if args.upload:
        upload_cforge(os.path.abspath(args.local_dir), args.repo_id)

    if args.download_model:
        download_model(args.model_name, args.save_dir, args.dtype)

    if not args.upload and not args.download_model:
        parser.print_help()


if __name__ == "__main__":
    main()
