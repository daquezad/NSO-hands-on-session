"""MkDocs hooks — Story 3.1: sitemap (NFR-S8). Story 3.3: paired blocks. Story 3.5: WebP + picture. Story 3.7: skip links + a11y landmarks. Story 5.1: learner vs instructor file sets (AR5). Story 5.4: inject Instructor artifacts nav when `INSTRUCTOR=1`. Story 6.3: PDF site data + print_page @page footers."""

from __future__ import annotations

import os
import re
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path

import logging

import yaml

from bs4 import BeautifulSoup, NavigableString, Tag
from mkdocs.structure.nav import Section, _add_parent_links, _add_previous_and_next_links
from mkdocs.structure.pages import Page

_LOG = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent

_CMD_LANG_PREFIX = ("language-bash", "language-shell", "language-cli")
_OUT_LANG_PREFIX = ("language-text", "language-console")

_EXPECTED_P_RE = re.compile(r"^\s*expected\s+output\s*:?\s*$", re.I)


def _is_instructor_build() -> bool:
    """True when `make build-instructor` / `INSTRUCTOR=1` is set (dual-audience instructor site)."""
    return os.environ.get("INSTRUCTOR", "").strip().lower() in ("1", "true", "yes")


def _read_nso_version_for_pdf() -> str:
    """Canonical NSO version for PDF footers — matches `scripts/pdf_build.read_nso_version`."""
    vf = _REPO_ROOT / "_data" / "versions.yaml"
    if vf.is_file():
        data = yaml.safe_load(vf.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("nso_version"):
            return str(data["nso_version"]).strip()
    m = re.search(r"nso_version:\s*[\"']?([^\"'\\s]+)", (_REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    if m:
        return m.group(1).strip()
    return "6.3"


def _css_content_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def on_config(config, **kwargs):  # type: ignore[no-untyped-def]
    """
    Merge `_data/site.yaml` into `extra`, set `pdf_build_date` (UTC), and align `nso_version`
    with `_data/versions.yaml` for print-site cover + PDF (Story 6.3).
    """
    extra = config.setdefault("extra", {})

    site_data = _REPO_ROOT / "_data" / "site.yaml"
    if site_data.is_file():
        raw = yaml.safe_load(site_data.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for k, v in raw.items():
                extra[k] = v

    extra["nso_version"] = _read_nso_version_for_pdf()

    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.strip().isdigit():
        dt = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    extra["pdf_build_date"] = dt.strftime("%Y-%m-%d")

    return config


def _inject_pdf_print_page_margin_css(site_dir: str) -> None:
    """
    Chromium PDF: `@page` margin text must be static CSS — inject NSO version from `_data/versions.yaml`.
    Clears default print-site-material @bottom-* on page 1 (cover) to avoid duplicating the banner.
    """
    html_path = Path(site_dir) / "print_page" / "index.html"
    if not html_path.is_file():
        return
    raw = html_path.read_text(encoding="utf-8")
    if 'id="pdf-page-margin-footer"' in raw:
        return

    ver = _read_nso_version_for_pdf()
    right_label = _css_content_escape(f"NSO {ver}")

    block = f"""<style id="pdf-page-margin-footer">
@page :first {{
  @bottom-left {{ content: none; }}
  @bottom-center {{ content: none; }}
  @bottom-right {{ content: none; }}
}}
@page {{
  @bottom-center {{ content: none; }}
  @bottom-left {{
    content: "Cisco Confidential";
    font-size: 8pt;
    font-family: "Inter", "Cisco Sans", "CiscoSansTT", sans-serif;
  }}
  @bottom-right {{
    content: "{right_label}";
    font-size: 8pt;
    font-family: "Inter", "Cisco Sans", "CiscoSansTT", sans-serif;
  }}
}}
</style>
"""
    if "</head>" in raw:
        html_path.write_text(raw.replace("</head>", block + "\n</head>", 1), encoding="utf-8")
    else:
        _LOG.warning("print_page/index.html has no </head>; skipping PDF margin CSS injection")


def on_files(files, *, config):  # type: ignore[no-untyped-def]
    """
    Learner builds omit facilitator-only Markdown:
    - everything under `docs/instructor-artifacts/`
    - chapter companion files `*-instructor-notes.md` next to lab chapters

    Instructor builds (`INSTRUCTOR=1`) include all of the above. AR5 / Story 5.1.
    """
    if _is_instructor_build():
        return files
    remove = []
    for f in files:
        uri = f.src_uri.replace("\\", "/")
        if uri.startswith("instructor-artifacts/") or uri.endswith("-instructor-notes.md"):
            remove.append(f)
    for f in remove:
        files.remove(f)
    return files


def _collect_nav_pages(items: list[object]) -> list[Page]:
    out: list[Page] = []
    for item in items:
        if isinstance(item, Page):
            out.append(item)
        elif isinstance(item, Section) and item.children:
            out.extend(_collect_nav_pages(item.children))
    return out


def on_nav(nav, /, *, config, files):  # type: ignore[no-untyped-def]
    """
    Instructor builds inject the **Instructor artifacts** nav section (Stories 5.4–5.5).
    Learner builds omit `instructor-artifacts/**` in `on_files`, so those paths are not
    listed in `mkdocs.yml` nav — avoids strict-mode warnings for missing nav targets.
    """
    if not _is_instructor_build():
        return nav

    idx = files.get_file_from_path("instructor-artifacts/index.md")
    pr = files.get_file_from_path("instructor-artifacts/proctor-checklist.md")
    ts = files.get_file_from_path("instructor-artifacts/timing-sheet.md")
    if (
        idx is None
        or pr is None
        or ts is None
        or idx.page is None
        or pr.page is None
        or ts.page is None
    ):
        _LOG.warning(
            "Instructor build: instructor-artifacts pages missing; skipping Instructor artifacts nav."
        )
        return nav

    overview = idx.page
    checklist = pr.page
    timing = ts.page
    section = Section("Instructor artifacts", [overview, checklist, timing])
    if not nav.items:
        nav.items[:] = [section]
    else:
        nav.items[:] = [nav.items[0], section, *nav.items[1:]]
    new_pages = _collect_nav_pages(nav.items)
    _add_parent_links(nav.items)
    _add_previous_and_next_links(new_pages)
    nav.pages[:] = new_pages
    return nav


def _generate_webp_for_pngs(site_dir: str) -> None:
    cwebp = shutil.which("cwebp")
    if not cwebp:
        return
    for root, _, files in os.walk(site_dir):
        for name in files:
            if not name.lower().endswith(".png"):
                continue
            png_path = os.path.join(root, name)
            webp_path = png_path[:-4] + ".webp"
            if os.path.isfile(webp_path):
                continue
            subprocess.run(
                [cwebp, "-quiet", "-q", "82", "-o", webp_path, png_path],
                check=False,
                capture_output=True,
            )


def _wrap_png_images_with_picture(site_dir: str) -> None:
    """After WebP siblings exist, wrap PNG <img> in <picture> for assets/images (Story 3.5)."""
    site_path = Path(site_dir)
    for html_path in site_path.rglob("*.html"):
        try:
            raw = html_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "assets/images/" not in raw or ".png" not in raw.lower():
            continue
        soup = BeautifulSoup(raw, "html.parser")
        changed = False
        for img in list(soup.find_all("img")):
            if img.find_parent("picture"):
                continue
            src = (img.get("src") or "").strip()
            if "assets/images/" not in src or ".png" not in src.lower():
                continue
            try:
                abs_png = (html_path.parent / src).resolve()
            except (OSError, ValueError):
                continue
            webp_path = abs_png.with_suffix(".webp")
            if not webp_path.is_file():
                continue
            try:
                rel_webp = os.path.relpath(webp_path, html_path.parent)
            except ValueError:
                continue
            rel_webp = rel_webp.replace("\\", "/")
            picture = soup.new_tag("picture")
            source = soup.new_tag("source", attrs={"type": "image/webp", "srcset": rel_webp})
            picture.append(source)
            img.replace_with(picture)
            picture.append(img)
            changed = True
        if changed:
            html_path.write_text(str(soup), encoding="utf-8")


def on_post_build(*, config) -> None:
    site_dir = config.site_dir
    for name in ("sitemap.xml", "sitemap.xml.gz"):
        path = os.path.join(site_dir, name)
        if os.path.isfile(path):
            os.remove(path)
    _generate_webp_for_pngs(site_dir)
    _wrap_png_images_with_picture(site_dir)
    _inject_pdf_print_page_margin_css(site_dir)


def _classes(el: Tag) -> list[str]:
    c = el.get("class")
    if not c:
        return []
    return c if isinstance(c, list) else [c]


def _inside_paired(div: Tag) -> bool:
    p = div.parent
    while p is not None:
        if p.name == "div" and "paired" in _classes(p):
            return True
        p = p.parent
    return False


def _is_command_highlight(div: Tag) -> bool:
    if div.name != "div" or "highlight" not in _classes(div):
        return False
    cs = " ".join(_classes(div))
    return any(x in cs for x in _CMD_LANG_PREFIX)


def _is_output_highlight(div: Tag) -> bool:
    if div.name != "div" or "highlight" not in _classes(div):
        return False
    cs = " ".join(_classes(div))
    return any(x in cs for x in _OUT_LANG_PREFIX)


def _skip_ws_sibling(node: object) -> object:
    while node is not None and isinstance(node, NavigableString) and not str(node).strip():
        node = node.next_sibling
    return node


def _p_expected_output_text(p: Tag | None) -> bool:
    if p is None or p.name != "p":
        return False
    text = p.get_text(strip=True)
    return bool(_EXPECTED_P_RE.match(text))


def _line_count_code_block(div: Tag) -> int:
    code = div.find("code")
    if code is None:
        return 0
    return max(1, len(code.get_text().splitlines()))


def _page_is_home(page: object) -> bool:
    return bool(getattr(page, "is_homepage", False))


def _enhance_a11y(html: str, page: object) -> str:
    """Story 3.7: skip links, nav/verification landmarks, stable heading id for Verification."""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return html

    has_verification = False
    for h2 in soup.find_all("h2"):
        t = re.sub(r"\s+", " ", h2.get_text(strip=True)).lower()
        t = t.replace("¶", "").replace("\u00b6", "").strip()
        if t == "verification" or t.startswith("verification "):
            has_verification = True
            if not h2.get("id"):
                h2["id"] = "verification"
            break

    primary = soup.find(attrs={"data-md-type": "navigation"})
    if isinstance(primary, Tag) and not primary.get("id"):
        primary["id"] = "workbook-navigation"

    skip = soup.find(attrs={"data-md-component": "skip"})
    if isinstance(skip, Tag):
        existing = {a.get("href") for a in skip.find_all("a") if a.get("href")}
        if soup.find(attrs={"data-md-type": "navigation"}) and "#workbook-navigation" not in existing:
            a_nav = soup.new_tag(
                "a",
                attrs={
                    "href": "#workbook-navigation",
                    "class": "md-skip",
                },
            )
            a_nav.string = "Skip to navigation"
            skip.append(a_nav)
        if (
            not _page_is_home(page)
            and has_verification
            and "#verification" not in existing
        ):
            a_ver = soup.new_tag(
                "a",
                attrs={
                    "href": "#verification",
                    "class": "md-skip",
                },
            )
            a_ver.string = "Skip to verification"
            skip.append(a_ver)

    return str(soup)


def _transform_paired_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    roots = soup.find_all(class_="md-content__inner")
    if not roots:
        roots = soup.find_all("article")
    if not roots:
        roots = [soup]

    for root in roots:
        for div in list(root.find_all("div", class_="highlight")):
            if not _is_command_highlight(div) or _inside_paired(div):
                continue

            cur = _skip_ws_sibling(div.next_sibling)
            landmark = ""
            marker_p: Tag | None = None
            if cur and getattr(cur, "name", None) == "p" and cur.find("span", class_="paired-landmark"):
                span = cur.find("span", class_="paired-landmark")
                landmark = ((span.get("data-landmark") or "") if span else "").strip()[:60]
                marker_p = cur
                cur = _skip_ws_sibling(cur.next_sibling)

            if not _p_expected_output_text(cur if isinstance(cur, Tag) else None):
                continue

            expected_p = cur
            nxt = _skip_ws_sibling(expected_p.next_sibling)
            if not isinstance(nxt, Tag) or not _is_output_highlight(nxt):
                continue

            parent = div.parent
            if parent is None:
                continue

            long_out = _line_count_code_block(nxt) >= 40
            head_cls = "paired__output-head"
            if long_out:
                head_cls += " paired__output-head--sticky"

            paired = soup.new_tag(
                "div",
                attrs={
                    "class": "paired",
                    "role": "group",
                    "aria-label": "Command and expected output",
                },
            )
            cmd_wrap = soup.new_tag("div", attrs={"class": "paired__command"})
            out_wrap = soup.new_tag("div", attrs={"class": "paired__output"})
            head = soup.new_tag("div", attrs={"class": head_cls})
            lbl = soup.new_tag("span", attrs={"class": "paired__label"})
            lbl.string = "\u2193 Expected output"
            head.append(lbl)
            if landmark:
                lm_span = soup.new_tag("span", attrs={"class": "paired__landmark-hint"})
                code_lm = soup.new_tag("code")
                code_lm.string = landmark
                lm_span.append("Look for: ")
                lm_span.append(code_lm)
                head.append(lm_span)

            body = soup.new_tag("div", attrs={"class": "paired__output-body"})
            live = soup.new_tag(
                "div",
                attrs={
                    "class": "paired__live paired__live--sr",
                    "aria-live": "polite",
                    "aria-atomic": "true",
                },
            )

            div.insert_before(paired)
            div.extract()
            if marker_p is not None:
                marker_p.extract()
            expected_p.extract()
            nxt.extract()

            cmd_wrap.append(div)
            body.append(nxt)
            out_wrap.append(head)
            out_wrap.append(body)
            out_wrap.append(live)
            paired.append(cmd_wrap)
            paired.append(out_wrap)

    return str(soup)


def on_post_page(output: str, /, *, page, config) -> str:  # type: ignore[no-untyped-def]
    if not output:
        return output
    try:
        out = output
        if "highlight" in output:
            out = _transform_paired_html(out)
        return _enhance_a11y(out, page)
    except Exception:
        return output
