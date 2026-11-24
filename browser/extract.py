"""Content-extraction helpers. Pure functions over a Playwright page object, so
they're easy to unit-test with a mock page (no real browser needed)."""
from __future__ import annotations


def readable_text(page) -> str:
    """The visible text of the page body, whitespace-collapsed."""
    try:
        txt = page.inner_text("body")
    except Exception:  # noqa: BLE001 - page may have no body / be odd; degrade
        txt = page.content() if hasattr(page, "content") else ""
    return " ".join((txt or "").split())


def all_links(page, base_url: str = "") -> list[str]:
    """Absolute href values of anchors on the page."""
    try:
        hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    except Exception:  # noqa: BLE001
        hrefs = []
    # Dedupe, keep order.
    seen, out = set(), []
    for h in hrefs or []:
        if h and h not in seen:
            seen.add(h)
            out.append(h)
    return out


def by_selectors(page, selectors: dict[str, str]) -> dict[str, str]:
    """Pull named fields by CSS selector, e.g. {'title':'h1','reqs':'.requirements'}.
    Missing selectors yield '' rather than erroring."""
    out: dict[str, str] = {}
    for name, sel in (selectors or {}).items():
        try:
            el = page.query_selector(sel)
            out[name] = " ".join((el.inner_text() or "").split()) if el else ""
        except Exception:  # noqa: BLE001
            out[name] = ""
    return out
