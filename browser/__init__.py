"""aegis-browser — a general, domain-agnostic headless browser wrapper.

Drives a browser to READ public pages (navigate, extract text/structure,
screenshot). It knows nothing about jobs or any domain — Aegis and its skills
(jobify, later learn++) call it. Hard rule: public-page reading only; no login,
no form-fill, no submit (see safety.py and DESIGN.md §2).
"""
from .client import BrowserClient, PageResult
from .safety import UnsafeUrlError, is_safe_to_read

__all__ = ["BrowserClient", "PageResult", "UnsafeUrlError", "is_safe_to_read"]
