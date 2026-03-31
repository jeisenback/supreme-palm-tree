#!/usr/bin/env python3
"""Export ECBA markdown docs to human-readable HTML while preserving cross-links.

- Scans etn/ECBA_CaseStudy for .md files
- Writes .html files to etn/ECBA_CaseStudy_Package_HTML with same relative paths
- Rewrites internal links from .md to .html
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path("etn/ECBA_CaseStudy")
OUT_ROOT = Path("etn/ECBA_CaseStudy_Package_HTML")


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"\*(.+?)\*")
CODE_RE = re.compile(r"`([^`]+)`")
FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

# Full-detail docs for Session 1 only, plus high-level overviews for the rest.
HIGH_LEVEL_DOCS = {
    "README.md",
    "ECBA_CaseStudy_Plan.md",
    "ECBA_CaseStudy_Consolidated_Plan.md",
    "ECBA_Series_Brief.md",
    "OnePager_MicroExpeditions.md",
    "Session0_Onboarding_Handout.md",
    "Personas.md",
    "Workshop_Handout.md",
    "TrailBlaze_MasterContext.md",
}


def rewrite_link_target(target: str) -> str:
    if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
        return target

    if "#" in target:
        base, anchor = target.split("#", 1)
        if base.lower().endswith(".md"):
            base = base[:-3] + ".html"
        return f"{base}#{anchor}"

    if target.lower().endswith(".md"):
        return target[:-3] + ".html"
    return target


def apply_inline(text: str) -> str:
    safe = html.escape(text)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target = rewrite_link_target(match.group(2))
        return f'<a href="{html.escape(target, quote=True)}">{html.escape(label)}</a>'

    safe = LINK_RE.sub(replace_link, safe)
    safe = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", safe)
    safe = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", safe)
    safe = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", safe)
    return safe


def is_table_sep(line: str) -> bool:
    # Matches markdown separator row like |---|---:|:---:|
    stripped = line.strip()
    if "|" not in stripped:
        return False
    parts = [p.strip() for p in stripped.strip("|").split("|")]
    if not parts:
        return False
    return all(re.fullmatch(r":?-{3,}:?", p) is not None for p in parts)


def parse_table_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def markdown_to_html(md_text: str, title: str) -> str:
    # Hide YAML frontmatter in exported human-readable docs.
    md_text = FRONTMATTER_RE.sub("", md_text, count=1)
    lines = md_text.splitlines()
    out: list[str] = []

    i = 0
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Blank line
        if not stripped:
            close_lists()
            i += 1
            continue

        # Heading
        if stripped.startswith("#"):
            close_lists()
            hashes = len(stripped) - len(stripped.lstrip("#"))
            level = min(max(hashes, 1), 6)
            text = stripped[hashes:].strip()
            out.append(f"<h{level}>{apply_inline(text)}</h{level}>")
            i += 1
            continue

        # Table (header + separator + rows)
        if i + 1 < len(lines) and "|" in lines[i] and is_table_sep(lines[i + 1]):
            close_lists()
            headers = parse_table_row(lines[i])
            out.append("<table>")
            out.append("<thead><tr>" + "".join(f"<th>{apply_inline(h)}</th>" for h in headers) + "</tr></thead>")
            out.append("<tbody>")
            i += 2
            while i < len(lines) and "|" in lines[i].strip() and lines[i].strip() and not lines[i].strip().startswith("#"):
                cells = parse_table_row(lines[i])
                out.append("<tr>" + "".join(f"<td>{apply_inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue

        # Unordered list
        if stripped.startswith(("- ", "* ")):
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{apply_inline(stripped[2:].strip())}</li>")
            i += 1
            continue

        # Ordered list
        if re.match(r"\d+\.\s+", stripped):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            item_text = re.sub(r"^\d+\.\s+", "", stripped)
            out.append(f"<li>{apply_inline(item_text)}</li>")
            i += 1
            continue

        # Horizontal rule
        if stripped in {"---", "***", "___"}:
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        # Paragraph
        close_lists()
        para_lines = [stripped]
        j = i + 1
        while j < len(lines):
            nxt = lines[j].strip()
            if not nxt:
                break
            if nxt.startswith("#") or nxt.startswith(("- ", "* ")) or re.match(r"\d+\.\s+", nxt):
                break
            if j + 1 < len(lines) and "|" in lines[j] and is_table_sep(lines[j + 1]):
                break
            para_lines.append(nxt)
            j += 1
        out.append(f"<p>{apply_inline(' '.join(para_lines))}</p>")
        i = j

    close_lists()

    style = """
body { font-family: 'Segoe UI', Tahoma, Arial, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 24px; line-height: 1.6; color: #1a1a1a; }
h1, h2, h3, h4 { line-height: 1.25; }
code { background: #f4f4f4; padding: 2px 5px; border-radius: 4px; }
a { color: #005ea2; text-decoration: none; }
a:hover { text-decoration: underline; }
table { border-collapse: collapse; width: 100%; margin: 16px 0; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
th { background: #f7f7f7; }
hr { border: 0; border-top: 1px solid #ddd; margin: 24px 0; }
""".strip()

    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"  <title>{html.escape(title)}</title>\n"
        f"  <style>{style}</style>\n"
        "</head>\n"
        "<body>\n"
        + "\n".join(out)
        + "\n</body>\n</html>\n"
    )


def should_include_md(md_file: Path) -> bool:
    rel = md_file.relative_to(ROOT)
    rel_posix = rel.as_posix()
    name = rel.name

    if name in HIGH_LEVEL_DOCS:
        return True

    # Include all Session 1 materials (participant + facilitator).
    if "Session1" in name:
        return True
    if rel_posix.startswith("Facilitator/") and "Session1" in name:
        return True

    return False


def export_all() -> None:
    md_files = sorted(f for f in ROOT.rglob("*.md") if should_include_md(f))
    if not md_files:
        raise SystemExit(f"No markdown files found under {ROOT}")

    # Ensure output contains only the current inclusion scope.
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)

    for md_file in md_files:
        rel = md_file.relative_to(ROOT)
        out_file = OUT_ROOT / rel.with_suffix(".html")
        out_file.parent.mkdir(parents=True, exist_ok=True)

        text = md_file.read_text(encoding="utf-8")
        title = rel.stem.replace("_", " ")
        html_doc = markdown_to_html(text, title)
        out_file.write_text(html_doc, encoding="utf-8")

    # Add a simple package index
    index_items = []
    for f in sorted(OUT_ROOT.rglob("*.html")):
        rel = str(f.relative_to(OUT_ROOT)).replace("\\", "/")
        index_items.append(f'<li><a href="{html.escape(rel)}">{html.escape(rel)}</a></li>')
    index_doc = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>ECBA HTML Package</title><style>body{font-family:Segoe UI,Tahoma,Arial,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;} li{margin:6px 0;} a{color:#005ea2;text-decoration:none;} a:hover{text-decoration:underline;}</style></head><body>"
        "<h1>ECBA Human-Readable Package</h1><p>This package includes full Session 1 materials and high-level docs for later sessions. Internal links are preserved as HTML links.</p><ul>"
        + "\n".join(index_items)
        + "</ul></body></html>"
    )
    (OUT_ROOT / "index.html").write_text(index_doc, encoding="utf-8")


if __name__ == "__main__":
    export_all()
    print(f"Export complete: {OUT_ROOT}")
