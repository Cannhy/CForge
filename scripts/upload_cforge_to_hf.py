"""
Upload CForge dataset to HuggingFace Hub: cannhy/CForge

Prerequisites:
    pip install -U huggingface_hub
    huggingface-cli login            # paste a *write-scope* token
    # or:  export HF_TOKEN=hf_xxx... (the script will pick it up)

Usage:
    python scripts/upload_cforge_to_hf.py
    python scripts/upload_cforge_to_hf.py --repo cannhy/CForge
    python scripts/upload_cforge_to_hf.py --dry-run     # only show what would be uploaded

Notes:
    - Files >10MB are uploaded via Git-LFS automatically by huggingface_hub.
    - The upload is resumable: re-run the same command after a network hiccup.
    - .cache/ and any *.metadata / *.lock files are excluded.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Please install huggingface_hub:  pip install -U huggingface_hub",
          file=sys.stderr)
    sys.exit(1)


DEFAULT_LOCAL_DIR = Path(__file__).resolve().parent.parent / "CForge_data"
DEFAULT_REPO = "cannhy/CForge"

# Ignore patterns: cache, lock files, __pycache__, etc.
IGNORE_PATTERNS = [
    ".cache/*",
    "**/.cache/*",
    "**/__pycache__/*",
    "*.lock",
    "*.metadata",
    "*.bak",
    ".DS_Store",
    "**/.DS_Store",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local_dir", default=str(DEFAULT_LOCAL_DIR),
                        help="Local folder to upload (default: ./CForge_data)")
    parser.add_argument("--repo", default=DEFAULT_REPO,
                        help="HuggingFace dataset repo id (default: cannhy/CForge)")
    parser.add_argument("--branch", default="main", help="Target branch")
    parser.add_argument("--commit_message",
                        default="Upload CForge dataset (Introductory/Easy/Medium/Hard)")
    parser.add_argument("--private", action="store_true",
                        help="Create the repo as private if it does not exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be uploaded without doing it")
    args = parser.parse_args()

    local = Path(args.local_dir).resolve()
    if not local.is_dir():
        print(f"local_dir not found: {local}", file=sys.stderr)
        sys.exit(1)

    token = os.getenv("HF_TOKEN")  # also picks up the cached login automatically
    api = HfApi(token=token)

    print(f"Local dir : {local}")
    print(f"Repo      : {args.repo}  (branch: {args.branch})")
    print(f"Visibility: {'private' if args.private else 'public'}")
    print()

    # List the files that will be uploaded.
    files_to_upload = []
    for p in local.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(local).as_posix()
        if any(_match(rel, pat) for pat in IGNORE_PATTERNS):
            continue
        files_to_upload.append((rel, p.stat().st_size))

    print(f"Files to upload ({len(files_to_upload)}):")
    total = 0
    for rel, sz in sorted(files_to_upload):
        total += sz
        print(f"  {rel:60s}  {_human(sz):>10s}")
    print(f"  {'TOTAL':<60s}  {_human(total):>10s}")
    print()

    if args.dry_run:
        print("(dry-run) Nothing was uploaded.")
        return

    # Make sure the repo exists.
    print("Ensuring the dataset repo exists...")
    create_repo(
        repo_id=args.repo,
        repo_type="dataset",
        token=token,
        private=args.private,
        exist_ok=True,
    )

    print("Uploading (this may take a while; LFS handles large files)...")
    api.upload_folder(
        folder_path=str(local),
        repo_id=args.repo,
        repo_type="dataset",
        revision=args.branch,
        commit_message=args.commit_message,
        ignore_patterns=IGNORE_PATTERNS,
        # multi-commits=True automatically chunks giant uploads into multiple
        # smaller commits so a single network failure won't lose everything.
        # Available in huggingface_hub >= 0.20.
        # multi_commits=True,
        # multi_commits_verbose=True,
    )
    print("\n✓ Done.")
    print(f"View at: https://huggingface.co/datasets/{args.repo}/tree/{args.branch}")


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _match(path: str, pattern: str) -> bool:
    """Tiny glob matcher (supports * and **)."""
    import fnmatch
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch("/" + path, "/" + pattern)


if __name__ == "__main__":
    main()
