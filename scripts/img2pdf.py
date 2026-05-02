"""
Convert PNG/JPG/JPEG/WEBP images to PDF (1 PDF per image, same base name).

Usage:
    # Convert every image in a folder (default: ./pics -> ./pics_pdf)
    python scripts/img2pdf.py pics

    # Specify output folder
    python scripts/img2pdf.py pics -o pics_pdf

    # Merge all images into one multi-page PDF
    python scripts/img2pdf.py pics -o pics_pdf --merge all.pdf

    # Convert a single image
    python scripts/img2pdf.py pics/bj.png -o out

Notes:
    - PNG's transparent channel is flattened onto a white background.
    - The output PDF page size matches the image pixel size at 72 DPI
      (i.e. visually identical to the source when rendered).
    - Requires: Pillow  (pip install pillow)
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with:  pip install pillow", file=sys.stderr)
    sys.exit(1)


IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _load_flat(path: Path) -> Image.Image:
    """Open an image; flatten alpha to white; ensure RGB mode for PDF."""
    img = Image.open(path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1])
        return bg
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def convert_one(src: Path, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    out = dst_dir / (src.stem + ".pdf")
    img = _load_flat(src)
    img.save(out, "PDF", resolution=100.0)
    return out


def convert_merged(srcs: list[Path], out_pdf: Path) -> Path:
    if not srcs:
        raise ValueError("No source images to merge.")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    first, rest = srcs[0], srcs[1:]
    first_img = _load_flat(first)
    rest_imgs = [_load_flat(p) for p in rest]
    first_img.save(
        out_pdf,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=rest_imgs,
    )
    return out_pdf


def collect_images(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in IMG_EXTS else []
    return sorted(
        p for p in target.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS
    )


def main():
    parser = argparse.ArgumentParser(description="Convert images to PDF.")
    parser.add_argument("input", help="Image file or folder to convert")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output folder (default: <input>_pdf for folder, ./pdf for single file)",
    )
    parser.add_argument(
        "--merge",
        default=None,
        help="If set, merge all images into one multi-page PDF with this file name "
             "(relative to --output).",
    )
    args = parser.parse_args()

    src = Path(args.input).resolve()
    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_dir = Path(args.output).resolve()
    elif src.is_dir():
        out_dir = src.parent / (src.name + "_pdf")
    else:
        out_dir = src.parent / "pdf"

    images = collect_images(src)
    if not images:
        print(f"No supported images found in {src}", file=sys.stderr)
        sys.exit(1)

    if args.merge:
        out_pdf = out_dir / args.merge
        convert_merged(images, out_pdf)
        print(f"Merged {len(images)} images -> {out_pdf}")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in images:
            out = convert_one(p, out_dir)
            print(f"{p.name}  ->  {out}")
        print(f"\nDone. {len(images)} PDF(s) written to {out_dir}")


if __name__ == "__main__":
    main()
