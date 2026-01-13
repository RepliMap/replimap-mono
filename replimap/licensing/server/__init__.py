"""
Server-side licensing components.

This package contains reference implementations for server-side
license signing. These are NOT used in the client CLI - they are
provided as references for implementing the license server.

Components:
- signer.py: Ed25519 license signing implementation

SECURITY: The private key should NEVER be stored in this codebase.
Store it in your server's secure secrets (e.g., Cloudflare Worker secrets).
"""

from replimap.licensing.server.signer import LicenseSigner

__all__ = ["LicenseSigner"]
