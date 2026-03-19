"""Simple CLI to ingest documents and store Markdown + context."""
from __future__ import annotations

import argparse
import sys
from ingest import convert_file_to_md_context, store_conversion
from framework.projects import ensure_project_output


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(description="Ingest documents into Markdown + JSON context")
    p.add_argument("files", nargs="+", help="Files to ingest")
    p.add_argument("-o", "--out", default="output", help="Output directory")
    p.add_argument("--project", help="Project name to store outputs under <project>/converted/")
    args = p.parse_args(argv)

    # determine output base directory
    out_base = args.out
    if args.project:
        out_base = ensure_project_output(args.project, subpath="converted")

    for f in args.files:
        try:
            md, ctx, assets = convert_file_to_md_context(f)
            md_path, json_path = store_conversion(md, ctx, assets, f, str(out_base))
            print(f"Stored: {f} -> {md_path}, {json_path}")
        except Exception as e:
            print(f"Error processing {f}: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
