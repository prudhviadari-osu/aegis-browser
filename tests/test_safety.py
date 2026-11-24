"""The safety gate — the most important logic to lock down: headless must refuse
login/auth/account/apply pages and non-http schemes, and allow plain public pages."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from browser.safety import is_safe_to_read, require_safe, UnsafeUrlError

SAFE = [
    "https://medtronic.wd1.myworkdayjobs.com/MedtronicCareers",   # listing (read ok)
    "https://example.com/jobs/data-scientist",
    "https://www.company.com/about",
    "http://news.site/article/123",
]
UNSAFE = [
    "https://accounts.google.com/signin",          # auth host
    "https://example.com/login",                   # login path
    "https://example.com/account/settings",        # account path
    "https://x.com/oauth/authorize",               # oauth
    "https://co.myworkdayjobs.com/en-US/Site/apply/123",  # apply flow (extension's job)
    "ftp://files.example.com/x",                   # non-http scheme
    "javascript:alert(1)",                          # not a real page
    "not-a-url",
]


def test_safe_urls_allowed():
    for u in SAFE:
        assert is_safe_to_read(u) is True, f"should allow: {u}"
    print("  public pages allowed: OK")


def test_unsafe_urls_blocked():
    for u in UNSAFE:
        assert is_safe_to_read(u) is False, f"should block: {u}"
    print("  login/auth/account/apply/non-http blocked: OK")


def test_require_safe_raises_on_unsafe():
    with pytest.raises(UnsafeUrlError):
        require_safe("https://example.com/login")


def test_require_safe_passes_on_safe():
    require_safe("https://example.com/jobs/123")   # should not raise
    print("  require_safe gate behaves: OK")


if __name__ == "__main__":
    test_safe_urls_allowed()
    test_unsafe_urls_blocked()
    test_require_safe_raises_on_unsafe()
    test_require_safe_passes_on_safe()
    print("\nSafety gate tests passed.")
