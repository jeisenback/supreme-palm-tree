"""Converters for different document types into Markdown and context objects."""
from __future__ import annotations

import io
import json
import mimetypes
import os
import pathlib
import re
from typing import Dict, Tuple, Optional

import mammoth
import html2text
from pypdf import PdfReader
import pandas as pd
from bs4 import BeautifulSoup


def _markdown_headings(md: str) -> list[str]:
    return re.findall(r"^#{1,6}\s+(.*)$", md, flags=re.M)


def _extract_headings_from_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in soup.find_all(re.compile(r'^h[1-6]$', re.I)):
        level = int(tag.name[1])
        text = tag.get_text(strip=True)
        headings.append({"level": level, "text": text})
    return headings


def _extract_sections_from_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    sections = {}
    current = None
    buf = []
    body = soup.body if soup.body else soup
    for elem in body.children:
        if getattr(elem, 'name', None) and re.match(r'^h[1-6]$', elem.name, re.I):
            if current:
                sections[current] = ''.join(str(x) for x in buf).strip()
            current = elem.get_text(strip=True)
            buf = []
        elif current:
            buf.append(elem)
    if current and buf:
        sections[current] = ''.join(str(x) for x in buf).strip()
    return sections


def _extract_tables_from_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    tables_out = []
    for tbl in soup.find_all('table'):
        rows = []
        for tr in tbl.find_all('tr'):
            cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            rows.append(cols)
        tables_out.append(rows)
    return tables_out


def convert_docx(path: pathlib.Path) -> Tuple[str, dict, Dict[str, bytes]]:
    assets: Dict[str, bytes] = {}
    image_count = 0

    def _image_converter(image):
        nonlocal image_count
        image_count += 1
        content_type = image.content_type or "application/octet-stream"
        ext = mimetypes.guess_extension(content_type.split(";")[0]) or ""
        name = f"image{image_count}{ext}"
        # robustly get bytes from mammoth image object
        data = None
        try:
            data = image.read()
        except Exception:
            try:
                fh = image.open()
                data = fh.read()
            except Exception:
                data = getattr(image, 'binary', None) or getattr(image, 'content', None)
        if data is None:
            return {"alt": image.alt_text or "", "src": ""}
        assets[name] = data
        return {"alt": image.alt_text or "", "src": name}

    with open(path, "rb") as f:
        result = mammoth.convert_to_html(f, convert_image=mammoth.images.inline(_image_converter))
    html = result.value

    # richer context extraction
    headings = _extract_headings_from_html(html)
    sections = _extract_sections_from_html(html)
    tables = _extract_tables_from_html(html)

    h = html2text.HTML2Text()
    h.body_width = 0
    h.wrap_links = False
    md = h.handle(html)

    context = {
        "title": path.stem,
        "headings": headings,
        "headings_flat": _markdown_headings(md),
        "sections_html": sections,
        "tables": tables,
        "images": list(assets.keys()),
    }
    return md, context, assets


def convert_pdf(path: pathlib.Path) -> Tuple[str, dict, Dict[str, bytes]]:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        try:
            text = p.extract_text() or ""
        except Exception:
            text = ""
        pages.append(text)
    md = "\n\n".join(pages)
    context = {"title": path.stem, "headings": _markdown_headings(md), "pages": len(pages)}
    return md, context, {}


def convert_txt(path: pathlib.Path) -> Tuple[str, dict, Dict[str, bytes]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    context = {"title": path.stem, "headings": _markdown_headings(text)}
    return text, context, {}


def convert_xlsx(path: pathlib.Path) -> Tuple[str, dict, Dict[str, bytes]]:
    # Read all sheets
    dfs = pd.read_excel(path, sheet_name=None)
    parts = []
    context_tables: Dict[str, list] = {}
    assets: Dict[str, bytes] = {}
    for sheet, df in dfs.items():
        parts.append(f"## {sheet}\n")
        try:
            parts.append(df.to_markdown(index=False))
        except Exception:
            parts.append(df.to_csv(index=False))

        # prepare JSON-serializable records
        def _serialize_value(v):
            if pd.isna(v):
                return None
            if isinstance(v, (pd.Timestamp, datetime.datetime, datetime.date)):
                try:
                    return v.isoformat()
                except Exception:
                    return str(v)
            return v

        try:
            records = []
            for _, row in df.iterrows():
                rec = {str(col): _serialize_value(row[col]) for col in df.columns}
                records.append(rec)
            context_tables[sheet] = records
        except Exception:
            context_tables[sheet] = []

        # create CSV bytes for this sheet as an asset
        try:
            csv_bytes = df.to_csv(index=False).encode('utf-8')
            asset_name = f"{re.sub(r'[^0-9A-Za-z_-]', '_', sheet).lower()}.csv"
            # avoid duplicate names
            if asset_name in assets:
                base = asset_name.rsplit('.csv', 1)[0]
                i = 1
                while f"{base}_{i}.csv" in assets:
                    i += 1
                asset_name = f"{base}_{i}.csv"
            assets[asset_name] = csv_bytes
        except Exception:
            pass

    md = "\n\n".join(parts)
    context = {"title": path.stem, "sheets": list(dfs.keys()), "tables": context_tables}
    return md, context, assets


def convert_file_to_md_context(path: str) -> Tuple[str, dict, Dict[str, bytes]]:
    p = pathlib.Path(path)
    suf = p.suffix.lower()
    if suf == ".docx":
        return convert_docx(p)
    if suf == ".pdf":
        return convert_pdf(p)
    if suf in {".txt", ".md"}:
        return convert_txt(p)
    if suf in {".xls", ".xlsx"}:
        return convert_xlsx(p)
    raise ValueError(f"Unsupported file type: {suf}")
