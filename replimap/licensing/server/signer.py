"""
Server-side license signing (Cloudflare Worker reference implementation).

This file is a REFERENCE for implementing the server-side signer.
It should be adapted to your Cloudflare Worker or backend service.

Security Requirements:
- Private key stored in Cloudflare Worker secrets
- Never expose private key in logs or responses
- Rate limit activation requests
- Validate payment/subscription status before signing

Cloudflare Worker Usage:
    export default {
        async fetch(request, env) {
            if (request.url.endsWith('/license/activate')) {
                return handleActivation(request, env);
            }
        }
    };
"""

from __future__ import annotations

import base64
import json
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

UTC = timezone.utc


class LicenseSigner:
    """
    Signs license blobs with Ed25519 private key.

    This is the SERVER-SIDE component.

    Usage (Python backend):
        signer = LicenseSigner(private_key_pem)

        blob = signer.sign_license(
            license_key="RM-SOLO-1234-ABCD",
            plan="solo",
            email="user@example.com",
            expires_days=365,
        )

        # Return blob to client

    For Cloudflare Worker, see the JavaScript implementation below.
    """

    def __init__(self, private_key_pem: bytes, key_id: str = "key-2024-01") -> None:
        """
        Initialize signer with private key.

        Args:
            private_key_pem: Ed25519 private key in PEM format
            key_id: Key ID for this key (for rotation)
        """
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        self.private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
        )

        if not isinstance(self.private_key, ed25519.Ed25519PrivateKey):
            raise ValueError("Key must be Ed25519")

        self.key_id = key_id

    def sign_license(
        self,
        license_key: str,
        plan: str,
        email: str,
        organization: str = "",
        expires_days: int = 365,
        features: Optional[list] = None,
        limits: Optional[dict] = None,
    ) -> str:
        """
        Sign a license and return the blob.

        Returns:
            License blob in format: payload_base64url.signature_base64url
        """
        now = datetime.now(UTC)
        now_ts = int(now.timestamp())
        exp_ts = now_ts + (expires_days * 86400)

        # Build payload
        payload: dict[str, Any] = {
            "v": 1,
            "kid": self.key_id,
            "lic": license_key,
            "plan": plan,
            "email": email,
            "org": organization,
            "iat": now_ts,
            "exp": exp_ts,
            "nbf": now_ts,
            "nonce": secrets.token_hex(8),
        }

        if features:
            payload["features"] = features

        if limits:
            payload["limits"] = limits

        # Serialize payload (sorted keys for consistency)
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_bytes = payload_json.encode("utf-8")

        # Sign
        signature = self.private_key.sign(payload_bytes)

        # Encode (base64url without padding)
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode("ascii")
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")

        return f"{payload_b64}.{signature_b64}"

    def sign_developer_license(
        self,
        email: str,
        expires_days: int = 7,
    ) -> str:
        """
        Sign a developer license.

        Developer licenses have:
        - Short expiration (default 7 days)
        - ENTERPRISE plan access
        - All features enabled

        Args:
            email: Developer email
            expires_days: Expiration in days

        Returns:
            License blob
        """
        return self.sign_license(
            license_key=f"DEV-{secrets.token_hex(4).upper()}",
            plan="enterprise",
            email=email,
            organization="Developer",
            expires_days=expires_days,
            features=None,  # Plan default includes all
            limits={
                "max_accounts": -1,
                "max_regions": -1,
                "max_resources_per_scan": -1,
                "max_concurrent_scans": -1,
                "max_scans_per_day": -1,
                "offline_grace_days": expires_days,
            },
        )


# ═══════════════════════════════════════════════════════════════════════════
# CLOUDFLARE WORKER IMPLEMENTATION (JavaScript)
# ═══════════════════════════════════════════════════════════════════════════

CLOUDFLARE_WORKER_CODE = '''
// Cloudflare Worker for license activation
// Store PRIVATE_KEY in Worker secrets

export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        if (url.pathname === '/v1/license/activate' && request.method === 'POST') {
            return handleActivation(request, env);
        }

        if (url.pathname === '/v1/license/developer' && request.method === 'POST') {
            return handleDeveloperLicense(request, env);
        }

        return new Response('Not Found', { status: 404 });
    }
};

async function handleActivation(request, env) {
    try {
        const body = await request.json();
        const { license_key, machine_info, cli_version } = body;

        // 1. Validate license key exists in database
        const license = await env.DB.prepare(
            'SELECT * FROM licenses WHERE key = ?'
        ).bind(license_key).first();

        if (!license) {
            return new Response(
                JSON.stringify({ error: 'Invalid license key' }),
                { status: 401, headers: { 'Content-Type': 'application/json' } }
            );
        }

        // 2. Check if license is active
        if (license.status !== 'active') {
            return new Response(
                JSON.stringify({ error: 'License is not active' }),
                { status: 403, headers: { 'Content-Type': 'application/json' } }
            );
        }

        // 3. Sign the license
        const blob = await signLicense(env.PRIVATE_KEY, {
            license_key: license.key,
            plan: license.plan,
            email: license.email,
            organization: license.organization,
            expires_at: license.expires_at,
        });

        // 4. Log activation
        await env.DB.prepare(
            'INSERT INTO activations (license_key, machine_info, cli_version, activated_at) VALUES (?, ?, ?, ?)'
        ).bind(license_key, JSON.stringify(machine_info), cli_version, Date.now()).run();

        return new Response(
            JSON.stringify({ license_blob: blob }),
            { status: 200, headers: { 'Content-Type': 'application/json' } }
        );

    } catch (error) {
        console.error('Activation error:', error);
        return new Response(
            JSON.stringify({ error: 'Internal server error' }),
            { status: 500, headers: { 'Content-Type': 'application/json' } }
        );
    }
}

async function signLicense(privateKeyPem, data) {
    // Import Ed25519 private key
    const privateKey = await crypto.subtle.importKey(
        'pkcs8',
        pemToArrayBuffer(privateKeyPem),
        { name: 'Ed25519' },
        false,
        ['sign']
    );

    // Build payload
    const now = Math.floor(Date.now() / 1000);
    const payload = {
        v: 1,
        kid: 'key-2024-01',
        lic: data.license_key,
        plan: data.plan,
        email: data.email,
        org: data.organization || '',
        iat: now,
        exp: data.expires_at ? Math.floor(new Date(data.expires_at).getTime() / 1000) : now + 31536000,
        nbf: now,
        nonce: crypto.randomUUID().replace(/-/g, '').slice(0, 16),
    };

    const payloadBytes = new TextEncoder().encode(JSON.stringify(payload));

    // Sign
    const signature = await crypto.subtle.sign(
        { name: 'Ed25519' },
        privateKey,
        payloadBytes
    );

    // Encode
    const payloadB64 = base64UrlEncode(payloadBytes);
    const signatureB64 = base64UrlEncode(new Uint8Array(signature));

    return `${payloadB64}.${signatureB64}`;
}

function pemToArrayBuffer(pem) {
    const b64 = pem.replace(/-----[A-Z ]+-----/g, '').replace(/\\s/g, '');
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}

function base64UrlEncode(bytes) {
    const binary = String.fromCharCode(...bytes);
    return btoa(binary).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=/g, '');
}
'''


def generate_worker_code() -> str:
    """Get Cloudflare Worker JavaScript code."""
    return CLOUDFLARE_WORKER_CODE


def print_worker_code() -> None:
    """Print Cloudflare Worker code to stdout."""
    print(CLOUDFLARE_WORKER_CODE)


if __name__ == "__main__":
    print("=" * 60)
    print("CLOUDFLARE WORKER CODE FOR LICENSE SIGNING")
    print("=" * 60)
    print_worker_code()
