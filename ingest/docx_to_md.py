#!/usr/bin/env python3
"""Simple DOCX -> Markdown converter using mammoth + html2text.

Usage:
  python docx_to_md.py input.docx           # writes input.md and assets folder
  python docx_to_md.py -o outdir file1.docx file2.docx
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import mimetypes
import itertools

import mammoth
import html2text


def convert_file(path: pathlib.Path, out_dir: pathlib.Path, extract_images: bool = True) -> pathlib.Path:
    stem = path.stem
    md_path = out_dir / f"{stem}.md"
    assets_dir = out_dir / f"{stem}_assets"
    if extract_images:
        assets_dir.mkdir(parents=True, exist_ok=True)

    image_count = itertools.count(1)

    def _image_converter(image):
        if not extract_images:
            return {"alt": image.alt_text or "", "src": ""}
        content_type = image.content_type or "application/octet-stream"
        ext = mimetypes.guess_extension(content_type.split(";")[0]) or ""
        idx = next(image_count)
        filename = f"image{idx}{ext}"
        out_path = assets_dir / filename
        with open(out_path, "wb") as f:
            f.write(image.read())
        # return relative path for the markdown
        rel = os.path.relpath(out_path, start=out_dir)
        return {"alt": image.alt_text or "", "src": rel}

    with open(path, "rb") as docx_file:
        if extract_images:
            result = mammoth.convert_to_html(docx_file, convert_image=mammoth.images.inline(_image_converter))
        else:
            result = mammoth.convert_to_html(docx_file)

    html = result.value

    # Convert HTML to Markdown
    h = html2text.HTML2Text()
    h.body_width = 0
    h.wrap_links = False
    md = h.handle(html)

    with open(md_path, "w", encoding="utf-8") as out_f:
        out_f.write(md)

    return md_path


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Convert .docx files to Markdown")
    parser.add_argument("files", nargs="+", help="Input .docx files")
    parser.add_argument("-o", "--out", default=".", help="Output directory")
    parser.add_argument("--no-images", dest="images", action="store_false", help="Do not extract images")
    args = parser.parse_args(argv)

    out_dir = pathlib.Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        p = pathlib.Path(f)
        if not p.exists():
            print(f"Skipping missing file: {p}", file=sys.stderr)
            continue
        try:
            md = convert_file(p, out_dir, extract_images=args.images)
            print(f"Converted: {p} -> {md}")
        except Exception as e:
            print(f"Error converting {p}: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
