# aegis-browser

A **general, domain-agnostic headless browser wrapper** (Playwright) for the Aegis
system. It drives a browser to **read public pages** — navigate, extract text and
structured fields, screenshot. It knows nothing about jobs or any domain; Aegis uses
it for research, and skills like **jobify** use it to read application pages.

Part of the three-repo system (map:
[aegis/docs/SYSTEM_DESIGN.md](https://github.com/prudhviadari-osu/aegis/blob/main/docs/SYSTEM_DESIGN.md)).
Full design: [DESIGN.md](DESIGN.md).

## The safety line (why this is safe to use)
- **Public-page reading only.** Every navigation passes a safety gate that **refuses
  login / auth / account / apply pages** and non-http URLs. Headless never logs into
  your accounts and never fills or submits a form.
- The actual **fill-and-review** of a live application is a separate browser
  **extension** (the `extension/` half, built later) that runs in *your* real session
  where *you* review and submit. Headless does the safe reading; you do the applying.

## Install
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium     # one-time browser download (for real use, not tests)
```

## Use it (general)
```python
from browser import BrowserClient

with BrowserClient() as b:
    page = b.fetch("https://example.com/jobs/data-scientist")   # a PUBLIC page
    print(page.title, page.text[:200], page.links)

    # pull specific fields by CSS selector
    fields = b.extract_structured(
        "https://example.com/jobs/123",
        {"title": "h1", "requirements": ".job-requirements"},
    )
```
`fetch()` returns a `PageResult` (`title`, `text`, `links`, `ok`, `error`). A normal
page error comes back as `ok=False` with a message; a blocked login/apply URL raises
`UnsafeUrlError` (a deliberate safety signal).

## How Aegis & jobify use it
- **Aegis** calls it directly for general research/reading (e.g. a future research skill).
- **jobify** (the jobs skill) calls it to read a *found* job's public requirements page
  while drafting an application. Job logic stays in jobify; browser-driving lives here.

## Tests
```bash
.venv/bin/python -m pytest tests/ -q
```
Tests run **without a real browser** (Playwright is imported lazily and mocked). They
cover the safety gate, extraction, and the fetch flow. Real-page behavior should be
verified by running it on your machine after `playwright install chromium`.

## Status
Headless wrapper + safety gate: built & tested. Next: jobify's application-prep uses
it; then the fill-and-review `extension/`.
