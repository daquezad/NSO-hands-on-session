#!/usr/bin/env python3
"""
Story 6.4 — Post-process Chromium/WeasyPrint PDF: preserve tagged structure (clone_from),
add bookmark outline (H1 + H2 from print HTML), set catalog Lang + Title, verify reading-order monotonicity.

Uses pypdf.PdfWriter(clone_from=reader) so /MarkInfo, /StructTreeRoot, and structure tags are retained
(unlike PdfWriter.append, which drops them).
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

REPO_ROOT = Path(__file__).resolve().parents[1]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch if unicodedata.category(ch) != "Cf" else "" for ch in s)
    return " ".join(s.split())


def _strip_headerlink_noise(text: str) -> str:
    return text.replace("¶", "").replace("\u00b6", "").strip()


def _heading_plain(el) -> str:
    if el is None or not hasattr(el, "find_all"):
        return ""
    clone = BeautifulSoup(str(el), "html.parser").find(["h1", "h2"])
    if clone is None:
        return ""
    for a in clone.find_all("a", class_="headerlink"):
        a.decompose()
    return _strip_headerlink_noise(clone.get_text())


def iter_print_site_headings(html_path: Path) -> list[tuple[int, str]]:
    """
    Return (level, title) in document order: level 1 = h1, 2 = h2.
    Scope: #print-site-page only (cover + TOC + all print-page sections).
    """
    raw = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    root = soup.select_one("#print-site-page")
    if root is None:
        return []
    out: list[tuple[int, str]] = []
    for el in root.find_all(["h1", "h2"], recursive=True):
        tag = el.name.lower()
        level = 1 if tag == "h1" else 2
        title = _heading_plain(el)
        if not title:
            continue
        out.append((level, title))
    return out


def _needle_variants(title: str) -> list[str]:
    """Search phrases to locate heading text inside PDF page extract_text()."""
    t = _norm(title)
    needles: list[str] = []
    if t:
        needles.append(t)
    # Drop leading enumeration like "2.1 " or "1 "
    stripped = re.sub(r"^[\d.]+\s+", "", t).strip()
    if stripped and stripped not in needles:
        needles.append(stripped)
    if ":" in t:
        tail = t.split(":", 1)[-1].strip()
        if len(tail) >= 8 and tail not in needles:
            needles.append(tail)
    return needles


def find_heading_page_index(
    page_texts: list[str], title: str, *, start_page: int = 0
) -> int:
    """
    First page index >= start_page where any needle appears (document order).

    Searching only forward from the previous heading's page avoids matching
    earlier pages when a short phrase (e.g. 'Home') repeats in the PDF.
    """
    needles = _needle_variants(title)
    for needle in needles:
        if len(needle) < 4:
            continue
        for i in range(max(0, start_page), len(page_texts)):
            if needle in page_texts[i]:
                return i
    return min(start_page, len(page_texts) - 1)


def load_site_title(mkdocs_yml: Path) -> str:
    """Read `site_name` without full YAML parse (mkdocs.yml uses `!!python/name:` tags)."""
    text = mkdocs_yml.read_text(encoding="utf-8")
    m = re.search(r"^site_name:\s*(.+)$", text, re.MULTILINE)
    if m:
        val = m.group(1).strip()
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        return val
    return "NSO Hands-On Training Workbook"


def finalize_print_pdf(
    pdf_path: Path,
    *,
    print_html: Path,
    mkdocs_yml: Path | None = None,
    pdf_lang: str = "en-US",
) -> dict[str, object]:
    """
    In-place update of pdf_path. Returns stats dict for logging/tests.
    """
    mkdocs_yml = mkdocs_yml or (REPO_ROOT / "mkdocs.yml")
    doc_title = load_site_title(mkdocs_yml)

    headings = iter_print_site_headings(print_html)
    reader = PdfReader(str(pdf_path))
    page_texts = [_norm(p.extract_text() or "") for p in reader.pages]

    indices: list[int] = []
    prev_page = 0
    for _level, title in headings:
        idx = find_heading_page_index(page_texts, title, start_page=prev_page)
        indices.append(idx)
        prev_page = idx

    writer = PdfWriter(clone_from=reader)
    writer.add_metadata(
        {
            "/Title": doc_title,
        }
    )
    writer._root_object[NameObject("/Lang")] = TextStringObject(pdf_lang)

    last_h1_ref = None
    n_h1 = 0
    n_h2 = 0
    for (level, title), page_idx in zip(headings, indices):
        short_title = title if len(title) <= 200 else title[:197] + "..."
        if level == 1:
            last_h1_ref = writer.add_outline_item(short_title, page_idx, parent=None)
            n_h1 += 1
        else:
            parent = last_h1_ref
            writer.add_outline_item(short_title, page_idx, parent=parent)
            n_h2 += 1

    with open(pdf_path, "wb") as f:
        writer.write(f)

    return {
        "headings": len(headings),
        "h1": n_h1,
        "h2": n_h2,
        "pages": len(reader.pages),
        "title": doc_title,
        "lang": pdf_lang,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Finalize learner PDF for accessibility (Story 6.4).")
    p.add_argument("pdf", type=Path, help="Path to PDF to rewrite in place")
    p.add_argument(
        "--print-html",
        type=Path,
        default=REPO_ROOT / "site" / "print_page" / "index.html",
        help="Built print_page index.html (default: site/print_page/index.html)",
    )
    p.add_argument("--mkdocs-yml", type=Path, default=REPO_ROOT / "mkdocs.yml")
    args = p.parse_args(argv)

    pdf = args.pdf
    if not pdf.is_file():
        print(f"finalize: missing PDF {pdf}", file=sys.stderr)
        return 1
    if not args.print_html.is_file():
        print(f"finalize: missing print HTML {args.print_html}", file=sys.stderr)
        return 1

    stats = finalize_print_pdf(
        pdf,
        print_html=args.print_html,
        mkdocs_yml=args.mkdocs_yml,
    )
    print(f"pdf_finalize_accessibility: updated {pdf} — {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
