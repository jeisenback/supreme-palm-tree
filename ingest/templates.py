"""Template utilities: simple placeholder rendering for Markdown templates.

We support templates as plain `.md` files with placeholders like `{{ key }}`.
Nested keys are supported using dot notation (e.g. `{{ author.name }}`), and
list indexing with numeric parts (e.g. `{{ headings_flat.0 }}`). This is a
lightweight alternative to Jinja2 for common use cases.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Dict, Union, Any


def load_template(path_or_text: Union[str, pathlib.Path]) -> str:
    p = pathlib.Path(path_or_text)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return str(path_or_text)


def _lookup(context: Dict[str, Any], key: str) -> Any:
    parts = key.split('.') if key else []
    cur: Any = context
    for part in parts:
        if cur is None:
            return ''
        # numeric index into list
        if re.fullmatch(r"\d+", part):
            idx = int(part)
            try:
                cur = cur[idx]
            except Exception:
                return ''
        else:
            if isinstance(cur, dict):
                cur = cur.get(part, '')
            else:
                # try attribute access
                cur = getattr(cur, part, '')
    return cur


_PH = re.compile(r"{{\s*([0-9A-Za-z_\.]+)\s*}}")


def render_template(template_text: str, context: Dict[str, Any]) -> str:
    def _repl(m: re.Match) -> str:
        key = m.group(1)
        val = _lookup(context, key)
        if val is None:
            return ''
        if isinstance(val, (list, dict)):
            try:
                return json.dumps(val, ensure_ascii=False)
            except Exception:
                return str(val)
        return str(val)

    return _PH.sub(_repl, template_text)


def render_template_from_files(template_path: Union[str, pathlib.Path], context_path: Union[str, pathlib.Path]) -> str:
    tpl_text = load_template(template_path)
    ctx = json.loads(pathlib.Path(context_path).read_text(encoding="utf-8"))
    return render_template(tpl_text, ctx)
