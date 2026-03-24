"""Generator utilities to produce documents/emails from templates and stored context."""
from __future__ import annotations

import json
import pathlib
from typing import Optional

from .templates import load_template, render_template


def generate_from_context_file(template_path: str | pathlib.Path, context_json: str | pathlib.Path, out_path: Optional[str | pathlib.Path] = None) -> pathlib.Path:
    tpl_text = load_template(template_path)
    ctx_path = pathlib.Path(context_json)
    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    rendered = render_template(tpl_text, ctx)

    if out_path is None:
        stem = ctx.get("title") or ctx_path.stem
        out_path = ctx_path.parent / f"{stem}_generated.md"

    out_path = pathlib.Path(out_path)
    out_path.write_text(rendered, encoding="utf-8")
    return out_path
