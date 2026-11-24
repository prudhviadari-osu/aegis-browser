"""BrowserClient — the general, domain-agnostic headless browser wrapper.

Thin layer over Playwright. Every navigation goes through the safety gate first,
so it can only READ public pages. Exposes general ops (fetch / extract_text /
extract_structured / screenshot) with no job/study concepts — Aegis uses it for
research, jobify uses it to read application pages.

Playwright is imported lazily inside _ensure_browser() so this module (and the
safety/extraction logic) can be imported and unit-tested without a browser installed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import extract
from .safety import require_safe


@dataclass
class PageResult:
    url: str
    final_url: str = ""
    title: str = ""
    text: str = ""
    links: list[str] = field(default_factory=list)
    ok: bool = True
    error: str = ""


class BrowserClient:
    def __init__(self, headless: bool = True, timeout: int = 20,
                 user_agent: str | None = None):
        self.headless = headless
        self.timeout_ms = timeout * 1000
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Apple Silicon) aegis-browser/0.1 (personal use)")
        self._pw = None
        self._browser = None
        self._context = None

    # --- lifecycle ---
    def _ensure_browser(self):
        if self._context is not None:
            return
        from playwright.sync_api import sync_playwright  # lazy: no import at module load
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(user_agent=self.user_agent)
        self._context.set_default_timeout(self.timeout_ms)

    def close(self) -> None:
        for obj, meth in ((self._context, "close"), (self._browser, "close"), (self._pw, "stop")):
            try:
                if obj is not None:
                    getattr(obj, meth)()
            except Exception:  # noqa: BLE001 - best-effort teardown
                pass
        self._context = self._browser = self._pw = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # --- the one place a page is opened (safety-gated) ---
    def _open(self, url: str):
        require_safe(url)            # raises UnsafeUrlError on login/auth/apply pages
        self._ensure_browser()
        page = self._context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        return page

    # --- general ops ---
    def fetch(self, url: str) -> PageResult:
        """Navigate to a PUBLIC url; return title/text/links. Never raises for a
        normal page error — returns ok=False with the message (so callers don't
        have to wrap every call). Only an UnsafeUrlError (a blocked login/apply
        page) propagates, because that's a programming/safety signal, not a page error."""
        page = None
        try:
            page = self._open(url)   # UnsafeUrlError propagates intentionally
            return PageResult(
                url=url, final_url=page.url, title=page.title(),
                text=extract.readable_text(page), links=extract.all_links(page), ok=True)
        except Exception as exc:     # noqa: BLE001 - any PAGE error -> ok=False
            from .safety import UnsafeUrlError
            if isinstance(exc, UnsafeUrlError):
                raise
            return PageResult(url=url, ok=False, error=str(exc))
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    pass

    def extract_text(self, url: str) -> str:
        return self.fetch(url).text

    def extract_structured(self, url: str, selectors: dict[str, str]) -> dict:
        page = None
        try:
            page = self._open(url)
            return extract.by_selectors(page, selectors)
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    pass

    def screenshot(self, url: str, path: str) -> str:
        page = None
        try:
            page = self._open(url)
            page.screenshot(path=path, full_page=True)
            return path
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:  # noqa: BLE001
                    pass
