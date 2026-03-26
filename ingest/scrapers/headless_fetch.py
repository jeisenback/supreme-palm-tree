"""headless_fetch.py — capture fully-rendered HTML via Playwright headless Chromium.

Usage (standalone):
    python -m ingest.scrapers.headless_fetch [--out DIR] [--timeout MS] [URL ...]

If no URLs are passed the script reads approved sources from
``config/sources-approved.yaml`` and fetches every allowed_path for sources
whose parser type contains "event" (or all sources when no parser filter is set).

Output
------
Each page is saved as  <out_dir>/<sanitised_filename>.html  and a JSON index
``<out_dir>/index.json`` maps  sanitised_filename -> absolute_url.

Returns (when imported)
-----------------------
``fetch_urls(urls, out_dir, timeout_ms)`` -> dict[str, str]
    filename -> rendered HTML string  (files are also written to disk)
"""
from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitise(url: str) -> str:
    """Turn a URL into a safe filename stem (no extension)."""
    s = re.sub(r"https?://", "", url)
    s = re.sub(r"[^\w\-]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:120]  # cap length


def _load_approved_urls(config_path: Optional[Path] = None) -> list[str]:
    """Return event page URLs derived from sources-approved.yaml."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config" / "sources-approved.yaml"

    if not config_path.exists():
        return []

    with open(config_path, encoding="utf-8") as fh:
        sources = yaml.safe_load(fh) or []

    from urllib.parse import urlparse as _urlparse

    urls: list[str] = []
    for src in sources:
        raw = src.get("url", "").rstrip("/")
        if not raw:
            continue
        parsed = _urlparse(raw)
        # Use only scheme+host so allowed_paths are not doubled when the
        # source url already contains a path component.
        base = f"{parsed.scheme}://{parsed.netloc}"
        paths = src.get("allowed_paths", ["/"])
        for path in paths:
            urls.append(base + "/" + path.lstrip("/"))
    return urls


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------

def fetch_urls(
    urls: list[str],
    out_dir: Path,
    timeout_ms: int = 30_000,
    wait_until: str = "networkidle",
) -> dict[str, str]:
    """Fetch each URL with headless Chromium; return {filename: html}.

    Files are also written to *out_dir*.
    """
    from playwright.sync_api import sync_playwright  # lazy import

    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for url in urls:
            fname = _sanitise(url) + ".html"
            try:
                print(f"  -> fetching {url} ...", flush=True)
                page.goto(url, timeout=timeout_ms, wait_until=wait_until)
                html = page.content()
                (out_dir / fname).write_text(html, encoding="utf-8")
                results[fname] = html
                print(f"    saved {fname} ({len(html):,} bytes)")
            except Exception as exc:  # noqa: BLE001
                print(f"    ERROR fetching {url}: {exc}", file=sys.stderr)

        browser.close()

    # Write index
    index = {fname: url for fname, url in zip(results.keys(), urls[: len(results)])}
    (out_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nIndex written to {out_dir / 'index.json'}")
    return results


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Headless HTML fetcher via Playwright")
    parser.add_argument("urls", nargs="*", help="URLs to fetch (defaults to approved sources)")
    parser.add_argument(
        "--out",
        default="ingest/scrapers/event_pages",
        help="Output directory (default: ingest/scrapers/event_pages)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30_000,
        help="Per-page timeout in milliseconds (default: 30000)",
    )
    parser.add_argument(
        "--wait-until",
        default="networkidle",
        choices=["load", "domcontentloaded", "networkidle", "commit"],
        help="Playwright waitUntil strategy (default: networkidle)",
    )
    args = parser.parse_args(argv)

    urls: list[str] = args.urls or _load_approved_urls()
    if not urls:
        print("No URLs to fetch. Pass URLs as arguments or populate config/sources-approved.yaml.")
        sys.exit(1)

    print(f"Fetching {len(urls)} URL(s) -> {args.out}")
    results = fetch_urls(
        urls,
        out_dir=Path(args.out),
        timeout_ms=args.timeout,
        wait_until=args.wait_until,
    )
    print(f"\nDone. {len(results)} page(s) captured.")


if __name__ == "__main__":
    main()
