# PDF engine spike helpers (Story 6.1)

Not part of the normal build. Regenerate comparison PDFs locally when adjusting `spike-corpus.html`.

## Chromium (macOS example)

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HTML="$PWD/spike-corpus.html"
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/corpus-chromium.pdf" "file://$HTML"
```

## WeasyPrint (Docker, reproducible Linux stack)

```bash
docker run --rm -v "$PWD/../..:/work" -w /work/scripts/spike \
  python:3.12-slim-bookworm bash -c \
  'apt-get update -qq && apt-get install -y -qq weasyprint && weasyprint spike-corpus.html corpus-weasyprint.pdf'
```

## Baseline fixture for Story 6.2

After regenerating Chromium output from `spike-corpus.html`, copy to:

`tests/fixtures/pdf/acceptance-baseline.pdf`
