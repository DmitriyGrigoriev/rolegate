"""
This file contains a definition for Content-Security-Policy headers.

Read more about it:
https://developer.mozilla.org/ru/docs/Web/HTTP/Headers/Content-Security-Policy

We are using `django-csp` to provide these headers.
Docs: https://github.com/mozilla/django-csp
"""

from typing import Tuple

# These values might and will be redefined in `development.py` env:
CSP_SCRIPT_SRC: Tuple[str, ...] = ("'self'", "'unsafe-inline'", "'unsafe-eval'",)
CSP_FONT_SRC: Tuple[str, ...] = ("'self'", "data:",)
CSP_STYLE_SRC: Tuple[str, ...] = ("'self'", "'unsafe-inline'",)
CSP_CONNECT_SRC: Tuple[str, ...] = (
    "'self'",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://192.168.56.58:8000",
    "https://cdn.lordicon.com"
)
CSP_DEFAULT_SRC: Tuple[str, ...] = ("'none'",)
CSP_IMG_SRC: Tuple[str, ...] = ("'self'", "data:")
