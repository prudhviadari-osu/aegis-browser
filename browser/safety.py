"""The safety gate — the structural guarantee that headless only READS public
pages and never wanders into a login / authenticated flow.

The client calls is_safe_to_read() before navigating anywhere; an unsafe URL
raises UnsafeUrlError rather than loading. This is the enforcement point for
DESIGN.md §2 ('no logging into your accounts').
"""
from __future__ import annotations

import re
from urllib.parse import urlparse


class UnsafeUrlError(Exception):
    """Raised when a URL looks like a login/auth/account page (or isn't http(s))."""


# Path/host fragments that signal an authentication or account-management flow.
# If any appears, headless refuses to load the page.
_AUTH_PATH_SIGNALS = [
    "/login", "/signin", "/sign-in", "/log-in", "/logon", "/auth", "/oauth",
    "/sso", "/session", "/account", "/accounts", "/password", "/register",
    "/signup", "/sign-up", "/mfa", "/2fa", "/verify", "/authenticate",
    "/apply",            # application forms are the extension's job, not headless
    "/myworkdayjobs",    # workday APPLY flow requires login — read via the public listing only
]
_AUTH_HOST_SIGNALS = [
    "accounts.", "login.", "signin.", "auth.", "sso.", "id.", "secure.",
]


def is_safe_to_read(url: str) -> bool:
    """True if the URL is a plain public http(s) page we may READ. False for
    login/auth/account/apply pages or non-http schemes."""
    try:
        p = urlparse(url)
    except (ValueError, TypeError):
        return False
    if p.scheme not in ("http", "https"):
        return False
    if not p.netloc:
        return False
    host = p.netloc.lower()
    path = (p.path or "").lower()
    if any(h in host for h in _AUTH_HOST_SIGNALS):
        return False
    if any(sig in path for sig in _AUTH_PATH_SIGNALS):
        return False
    return True


def require_safe(url: str) -> None:
    """Raise UnsafeUrlError if the URL isn't safe to read. Call before navigating."""
    if not is_safe_to_read(url):
        raise UnsafeUrlError(
            f"Refusing to load '{url}': headless reads PUBLIC pages only — not "
            "login/auth/account/apply pages. Filling a live application is the "
            "browser extension's job, in your own session."
        )
