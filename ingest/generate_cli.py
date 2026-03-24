"""CLI to generate documents from templates and stored JSON context."""
from __future__ import annotations

import argparse
import sys
import pathlib
import json

from ingest.generator import generate_from_context_file
from framework.projects import get_project_dir


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Generate documents from templates and stored context")
    p.add_argument("-t", "--template", required=True, help="Template file or template text")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--context", help="Path to JSON context file")
    group.add_argument("--project", nargs=2, metavar=("PROJECT", "SOURCE_STEM"), help="Project name and source stem to locate stored JSON (project/converted/<stem>.json)")
    p.add_argument("-o", "--out", help="Output file path (optional)")
    args = p.parse_args(argv)

    context_path = None
    if args.context:
        context_path = pathlib.Path(args.context)
    else:
        proj, stem = args.project
        proj_dir = get_project_dir(proj)
        context_path = proj_dir / "converted" / f"{stem}.json"

    if not context_path.exists():
        print(f"Context JSON not found: {context_path}")
        return 2

    out = generate_from_context_file(args.template, context_path, args.out)
    print(f"Generated: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
