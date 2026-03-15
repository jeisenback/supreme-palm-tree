"""Storage utilities: write markdown, context JSON, and assets to disk.

Outputs are normalized to snake_case (filenames and asset folders). When a
normalized name already exists the new content overwrites the existing file
so older duplicates are replaced.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Dict, Tuple


def _normalize_stem(name: str) -> str:
    # remove trailing (n) patterns and weird characters, then snake_case
    s = re.sub(r"\s*\(\s*\d+\s*\)", "", name)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^0-9A-Za-z _-]", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower()


def _normalize_asset_name(name: str) -> str:
    # keep extension if present
    p = pathlib.Path(name)
    stem = p.stem
    ext = p.suffix
    s = re.sub(r"\s+", "_", stem).strip()
    s = re.sub(r"[^0-9A-Za-z _-]", "", s)
    s = re.sub(r"[\s-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower() + ext


def store_conversion(md_text: str, context: dict, assets: Dict[str, bytes], src_path: str, out_dir: str) -> Tuple[pathlib.Path, pathlib.Path]:
    out = pathlib.Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    src = pathlib.Path(src_path)
    stem = src.stem
    norm = _normalize_stem(stem)

    md_path = out / f"{norm}.md"
    json_path = out / f"{norm}.json"

    # write (overwrite) markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    # write (overwrite) json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    # write assets (csvs, images, etc.) into normalized assets folder
    if assets:
        assets_dir = out / f"{norm}_assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for name, data in assets.items():
            aname = _normalize_asset_name(name)
            with open(assets_dir / aname, "wb") as af:
                af.write(data)

    return md_path, json_path
