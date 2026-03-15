"""Simple project utilities: resolve project directories and outputs.

Assumes projects are folders at the workspace root (or subfolders). For now
we resolve by name to a sibling folder of this repository root.
"""
from __future__ import annotations

import pathlib
from typing import Optional


def get_project_dir(name: str, workspace_root: Optional[str] = None) -> pathlib.Path:
    """Return a Path to the project folder by name.

    If `workspace_root` is not provided, use the current working directory.
    """
    root = pathlib.Path(workspace_root) if workspace_root else pathlib.Path.cwd()
    candidate = root / name
    if candidate.exists() and candidate.is_dir():
        return candidate.resolve()
    # fallback: try to find a folder anywhere under root named `name`
    for p in root.iterdir():
        if p.is_dir() and p.name.lower() == name.lower():
            return p.resolve()
    # if not found, return path where it would live (do not create)
    return candidate.resolve()


def ensure_project_output(project_name: str, subpath: str = "converted", workspace_root: Optional[str] = None) -> pathlib.Path:
    """Ensure an output directory for a project and return it.

    `subpath` is the subfolder under the project dir to store outputs.
    """
    proj = get_project_dir(project_name, workspace_root=workspace_root)
    out = proj / subpath
    out.mkdir(parents=True, exist_ok=True)
    return out
