"""Simple CLI for agents tasks (PoC).

Commands:
- ingest --src PATH [--out OUT_DIR]

This module is intentionally small and synchronous; it's designed as an
administrative CLI to invoke the existing `ingest` pipeline.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from ingest.converters import convert_file_to_md_context
from ingest.storage import store_conversion


def cmd_ingest(src: str, out_dir: Optional[str] = None) -> int:
    """Ingest a single source file and store the conversion using existing pipeline.

    Returns exit code 0 on success, non-zero on failure.
    """
    try:
        md_text, context, assets = convert_file_to_md_context(src)
        out_path, json_path = store_conversion(md_text, context, assets, src, out_dir or "out")
        print(f"Ingested {src} -> {out_path} (context: {json_path})")
        return 0
    except Exception as e:
        print(f"Error ingesting {src}: {e}", file=sys.stderr)
        return 2


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="agents-cli")
    sub = parser.add_subparsers(dest="cmd")

    p_ingest = sub.add_parser("ingest", help="Ingest a file via the ingest pipeline")
    p_ingest.add_argument("--src", required=True, help="Path to source file to ingest")
    p_ingest.add_argument("--out", required=False, help="Output directory (default: out)")

    args = parser.parse_args(argv)
    if args.cmd == "ingest":
        return cmd_ingest(args.src, args.out)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
