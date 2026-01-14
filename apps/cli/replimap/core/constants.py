"""
RepliMap constants and configuration.

Single source of truth for contact information, URLs, and other constants.
Import from this module when displaying contact info, links, or product info.
"""

from __future__ import annotations

# Contact Information
EMAIL_GENERAL = "hello@replimap.com"
EMAIL_SUPPORT = "support@replimap.com"
EMAIL_SALES = "david@replimap.com"

# URLs
URL_HOMEPAGE = "https://replimap.com"
URL_DOCS = "https://replimap.com/docs"
URL_PRICING = "https://replimap.com/pricing"
URL_REPO = "https://github.com/RepliMap/replimap"
URL_ISSUES = "https://github.com/RepliMap/replimap/issues"
URL_DISCUSSIONS = "https://github.com/RepliMap/replimap/discussions"

# Product Info
PRODUCT_NAME = "RepliMap"
PRODUCT_TAGLINE = "AWS Infrastructure Intelligence Engine"
AUTHOR_NAME = "David Lu"

__all__ = [
    # Emails
    "EMAIL_GENERAL",
    "EMAIL_SUPPORT",
    "EMAIL_SALES",
    # URLs
    "URL_HOMEPAGE",
    "URL_DOCS",
    "URL_PRICING",
    "URL_REPO",
    "URL_ISSUES",
    "URL_DISCUSSIONS",
    # Product
    "PRODUCT_NAME",
    "PRODUCT_TAGLINE",
    "AUTHOR_NAME",
]
