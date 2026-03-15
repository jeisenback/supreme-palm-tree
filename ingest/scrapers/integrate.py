"""Integrate scraped items into the existing ingest/storage pipeline."""

from __future__ import annotations

from typing import Dict, Tuple

from ingest.storage import store_conversion


def integrate_scraped_item(item: Dict, src_identifier: str, out_dir: str | None = None) -> Tuple[str, str]:
    """Convert a scraped item into markdown + context and store it.

    Returns tuple of (md_path, json_path) as returned by `store_conversion`.

    Expected `item` keys: title, summary, date, location, source_url (optional).
    """
    title = item.get("title") or "Untitled"
    summary = item.get("summary") or ""
    date = item.get("date")
    location = item.get("location")
    source_url = item.get("source_url") or src_identifier

    md_lines = [f"# {title}", ""]
    if summary:
        md_lines.append(summary)
        md_lines.append("")

    if date:
        md_lines.append(f"**Date:** {date}  ")
    if location:
        md_lines.append(f"**Location:** {location}  ")

    md_lines.append("")
    md_lines.append(f"Source: {source_url}")

    md_text = "\n".join(md_lines)

    # Mark as external scraped content
    context = dict(item)
    context.setdefault("source", "external")

    assets: Dict[str, bytes] = {}

    return store_conversion(md_text, context, assets, str(source_url), out_dir or "out")
