# Validating `Workbook.pdf` against Markdown (internal)

Use the **PDF** the same way as **`Workbook-HT-v02.docx`**: extract assets, compare counts, and reconcile **example IPs** with the scrubbed site.

## Prerequisites

- **`Workbook.pdf`** at the repo root (or pass an explicit path). Note: **`*.pdf` is gitignored** — keep the file locally for validation; do not rely on it being in git.
- Python deps: **`pypdf`** (`pip install -r requirements.txt`).

## Scripts

| Script | Purpose |
|--------|---------|
| **`scripts/validate_workbook_pdf.py`** | Prints page count, embedded image count, optional comparison to **`.docx`** `word/media` count, keyword checks (`server-alias`, `sync-from`, `10.1.1.3`/`30`), and **PDF vs Markdown IP** notes. |
| **`scripts/extract_workbook_pdf_images.py`** | Writes raster images to **`build/workbook-pdf-media/`** (default; override `--out`). |
| **`scripts/extract_docx_media.py`** | Extracts **`word/media/*`** from a **`.docx`** (default output next to the file). |

Example:

```bash
python3 scripts/validate_workbook_pdf.py Workbook.pdf --docx Workbook-HT-v02.docx
python3 scripts/extract_workbook_pdf_images.py Workbook.pdf
```

## PDF section numbering vs Markdown labs

The **HT PDF** uses **1.1**, **1.2**, **1.3**, … in the table of contents. The Markdown chapters use **Lab 1–9** filenames. Common mapping:

| PDF (TOC) | Markdown |
|-----------|----------|
| 1 — Connect to the Workstation | `docs/01-connect-workstation.md` |
| 1.1 — Install NSO and NEDs | `docs/02-install-nso-neds.md` |
| 1.2 — Registering XRd routers | `docs/03-register-xrd-routers.md` |
| 1.3 — Configure Devices using NSO | `docs/04-configure-devices.md` |

## IP scrubbing (PDF vs site)

Exports may still contain **legacy lab IPs** (e.g. **198.18.x.x** in text extraction). The built workbook uses **RFC 5737 documentation** addresses (**198.51.100.x**) where examples are needed — see **`docs/scrub-logs/`** and chapter-specific scrub notes. **Class delivery** should follow the **facilitator lab sheet**, not a stale PDF literal.

## Related

- **`docs/scrub-protocol.md`** — screenshot / identifier scrub rules.
- **`docs/02-install-nso-neds.md`** — Web UI / `server-alias` (Step 6 in Markdown).
- **`docs/04-configure-devices.md`** — device IPv4 edit vs SSH management IP.
