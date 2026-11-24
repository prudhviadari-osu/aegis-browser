"""Extraction helpers + the client's fetch flow, tested with a MOCK Playwright
page (no real browser needed — the sandbox/CI has none). Verifies the safety gate
is enforced inside the client and that page errors degrade to ok=False."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from browser import extract
from browser.client import BrowserClient, PageResult
from browser.safety import UnsafeUrlError


# ---------- extraction helpers (pure, mock page) ----------
def _mock_page(text="Hello world  job", links=None, title="A Page", url="https://x/final"):
    page = MagicMock()
    page.inner_text.return_value = text
    page.eval_on_selector_all.return_value = links or ["https://x/a", "https://x/a", "https://x/b"]
    page.title.return_value = title
    page.url = url
    return page


def test_readable_text_collapses_whitespace():
    assert extract.readable_text(_mock_page(text="  a   b\n\n c ")) == "a b c"


def test_all_links_dedupes_preserves_order():
    links = extract.all_links(_mock_page(links=["https://x/a", "https://x/a", "https://x/b"]))
    assert links == ["https://x/a", "https://x/b"]


def test_by_selectors_missing_is_blank():
    page = MagicMock()
    def qs(sel):
        if sel == "h1":
            el = MagicMock(); el.inner_text.return_value = "Title Here"; return el
        return None
    page.query_selector.side_effect = qs
    out = extract.by_selectors(page, {"title": "h1", "missing": ".nope"})
    assert out == {"title": "Title Here", "missing": ""}
    print("  extraction helpers: OK")


# ---------- client.fetch flow (mock the _open page) ----------
def test_fetch_returns_pageresult(monkeypatch):
    c = BrowserClient()
    monkeypatch.setattr(c, "_open", lambda url: _mock_page())
    r = c.fetch("https://example.com/jobs/1")
    assert isinstance(r, PageResult) and r.ok is True
    assert r.text == "Hello world job" and r.title == "A Page"
    assert r.links == ["https://x/a", "https://x/b"]
    print("  fetch returns a populated PageResult: OK")


def test_fetch_unsafe_url_raises():
    """An UnsafeUrlError must PROPAGATE (safety signal), not be swallowed as ok=False."""
    c = BrowserClient()
    with pytest.raises(UnsafeUrlError):
        c.fetch("https://example.com/login")


def test_fetch_page_error_degrades(monkeypatch):
    """A normal page error returns ok=False with a message, doesn't raise."""
    c = BrowserClient()
    def boom(url):
        raise RuntimeError("timeout loading page")
    monkeypatch.setattr(c, "_open", boom)
    r = c.fetch("https://example.com/jobs/1")
    assert r.ok is False and "timeout" in r.error
    print("  page errors degrade to ok=False (safety errors still raise): OK")


if __name__ == "__main__":
    raise SystemExit(__import__("subprocess").call(
        ["python", "-m", "pytest", __file__, "-v"]))
