"""
Cryptographic components for license verification.

Security Model:
- Ed25519 digital signatures (asymmetric)
- Public key only on client (cannot forge signatures)
- Time validation (anti-tampering)
- Key rotation support

IMPORTANT: Private keys are NEVER stored in client code.
"""

from replimap.licensing.crypto.keys import KeyRegistry, generate_keypair
from replimap.licensing.crypto.time_validator import TimeValidationError, TimeValidator

__all__ = [
    "KeyRegistry",
    "generate_keypair",
    "TimeValidator",
    "TimeValidationError",
]
