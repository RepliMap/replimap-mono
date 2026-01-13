"""
Ed25519 Public Key Registry with rotation support.

Security Design:
- Multiple public keys indexed by Key ID (kid)
- Current key for new licenses
- Old keys still valid (for existing licenses)
- Revoked keys rejected
- No private keys in client code

Key Rotation Process:
1. Generate new keypair on server
2. Add public key to this registry with new kid
3. Update CURRENT_KEY_ID
4. Old licenses continue to work
5. Revoke old keys when all licenses expire
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class KeyRegistry:
    """
    Public key registry for Ed25519 license verification.

    Usage:
        # Get public key for verification
        public_key = KeyRegistry.get_public_key("key-2024-01")

        # Check if key is valid
        if KeyRegistry.is_key_valid("key-2023-01"):
            # Proceed with verification

    Key Format:
        PEM-encoded Ed25519 public key (SubjectPublicKeyInfo format)
    """

    # ═══════════════════════════════════════════════════════════════════
    # PUBLIC KEYS - Add new keys here during rotation
    # ═══════════════════════════════════════════════════════════════════

    PUBLIC_KEYS: dict[str, bytes] = {
        # Current active key (2024)
        "key-2024-01": b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAREPLACE_WITH_YOUR_ACTUAL_PUBLIC_KEY_HERE_32BYTES
-----END PUBLIC KEY-----""",
        # Previous key (still accepted for old licenses)
        # "key-2023-01": b"""-----BEGIN PUBLIC KEY-----
        # MCowBQYDK2VwAyEAOLD_KEY_HERE_FOR_BACKWARD_COMPATIBILITY_32B
        # -----END PUBLIC KEY-----""",
    }

    # Key ID used for signing new licenses (server-side reference)
    CURRENT_KEY_ID: str = "key-2024-01"

    # Revoked keys - signatures from these keys are ALWAYS rejected
    REVOKED_KEY_IDS: set[str] = set()
    # Example: {"key-2022-01"}  # Revoked due to compromise

    @classmethod
    def get_public_key(cls, kid: str) -> bytes | None:
        """
        Get public key PEM by Key ID.

        Args:
            kid: Key ID from license payload

        Returns:
            PEM bytes if key exists and not revoked, None otherwise
        """
        if kid in cls.REVOKED_KEY_IDS:
            logger.warning(f"Attempted to use revoked key: {kid}")
            return None

        return cls.PUBLIC_KEYS.get(kid)

    @classmethod
    def is_key_valid(cls, kid: str) -> bool:
        """Check if a key ID is valid (exists and not revoked)."""
        return kid not in cls.REVOKED_KEY_IDS and kid in cls.PUBLIC_KEYS

    @classmethod
    def get_all_valid_key_ids(cls) -> set[str]:
        """Get all valid (non-revoked) key IDs."""
        return set(cls.PUBLIC_KEYS.keys()) - cls.REVOKED_KEY_IDS

    @classmethod
    def verify_signature(
        cls,
        kid: str,
        signature: bytes,
        data: bytes,
    ) -> bool:
        """
        Verify Ed25519 signature using the specified key.

        Args:
            kid: Key ID
            signature: 64-byte Ed25519 signature
            data: Original signed data

        Returns:
            True if signature is valid, False otherwise
        """
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        public_key_pem = cls.get_public_key(kid)
        if not public_key_pem:
            logger.warning(f"Unknown or revoked key ID: {kid}")
            return False

        try:
            public_key = serialization.load_pem_public_key(public_key_pem)

            if not isinstance(public_key, ed25519.Ed25519PublicKey):
                logger.error(f"Key {kid} is not Ed25519")
                return False

            public_key.verify(signature, data)
            return True

        except InvalidSignature:
            logger.warning(f"Invalid signature for key {kid}")
            return False
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# KEY GENERATION UTILITY (Run once to generate keypair)
# ═══════════════════════════════════════════════════════════════════════════


def generate_keypair() -> tuple[bytes, bytes]:
    """
    Generate a new Ed25519 keypair.

    Returns:
        (private_key_pem, public_key_pem)

    Usage:
        private_pem, public_pem = generate_keypair()

        # Save private key to Cloudflare Worker secrets
        print("PRIVATE KEY (server only):")
        print(private_pem.decode())

        # Add public key to KeyRegistry.PUBLIC_KEYS
        print("PUBLIC KEY (add to keys.py):")
        print(public_pem.decode())

    SECURITY: Run this OFFLINE on a secure machine.
    NEVER commit private key to version control.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    # Generate private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    # Export private key (PEM format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Export public key (PEM format)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return private_pem, public_pem


if __name__ == "__main__":
    # Utility: Generate new keypair
    print("=" * 60)
    print("GENERATING NEW ED25519 KEYPAIR")
    print("=" * 60)

    private_pem, public_pem = generate_keypair()

    print("\nPRIVATE KEY (Store in Cloudflare Worker Secrets):")
    print("-" * 60)
    print(private_pem.decode())

    print("\nPUBLIC KEY (Add to KeyRegistry.PUBLIC_KEYS):")
    print("-" * 60)
    print(public_pem.decode())

    print("\nSECURITY REMINDER:")
    print("  - NEVER commit private key to version control")
    print("  - NEVER store private key in client code")
    print("  - Store private key in Cloudflare Worker secrets only")
