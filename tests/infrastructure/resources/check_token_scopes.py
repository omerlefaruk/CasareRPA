"""
Check OAuth token scopes for Gemini credential.
Run with: python tests/infrastructure/resources/check_token_scopes.py
"""

import asyncio
import base64
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def decode_jwt(token: str) -> dict | None:
    """Decode a JWT token without verification (for inspection only)."""
    try:
        # JWT has 3 parts: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode the payload (middle part)
        payload = parts[1]
        # Add padding if needed
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return None


async def main():
    from casare_rpa.infrastructure.security.credential_store import get_credential_store
    from casare_rpa.infrastructure.security.gemini_oauth import get_gemini_manager

    print("\n" + "=" * 70)
    print("GEMINI OAUTH TOKEN SCOPE CHECKER")
    print("=" * 70)

    # Find Google OAuth credentials
    store = get_credential_store()
    credentials = store.list_credentials()

    google_creds = [
        c for c in credentials if c.get("type") == "google_oauth" or c.get("category") == "google"
    ]

    if not google_creds:
        print("\n[!] No Google OAuth credentials found.")
        return

    for cred in google_creds:
        cred_id = cred["id"]
        print(f"\n{'=' * 70}")
        print(f"Credential: {cred.get('name')} (ID: {cred_id})")
        print(f"{'=' * 70}")

        # Get and decrypt credential data
        cred_data = store.get_credential(cred_id)
        if not cred_data:
            print("\n[!] Could not load credential data")
            continue

        # Extract access token from decrypted data
        access_token = cred_data.get("access_token", "")
        if access_token:
            # Decode JWT to see actual scopes
            decoded = decode_jwt(access_token)
            if decoded:
                print("\n[Token Payload]")
                print(f"  Issuer: {decoded.get('iss')}")
                print(f"  Audience: {decoded.get('aud')}")
                print(f"  Scope: {decoded.get('scope', '(not in token)')}")
                print(f"  Expires: {decoded.get('exp')}")

                # Check scopes
                scope_str = decoded.get("scope", "")
                scopes = scope_str.split() if scope_str else []

                print("\n[Scope Analysis]")
                has_cloud = any("cloud-platform" in s for s in scopes)
                has_gen = any("generative-language" in s for s in scopes)

                print(f"  cloud-platform scope: {'✓' if has_cloud else '✗'}")
                print(f"  generative-language scope: {'✓' if has_gen else '✗'}")

                if not has_gen:
                    print("\n[!] PROBLEM: Token missing generative-language scope!")
                    print("\n[Solution]")
                    print(
                        "  Your token was granted before the generative-language scope was added."
                    )
                    print("  Refresh tokens cannot add new scopes - you must re-authenticate.")
                    print("\n  Steps to fix:")
                    print("  1. Delete your existing Google credential")
                    print("  2. Re-connect with 'Connect Gemini AI Studio'")
                    print("  3. Approve BOTH scopes when prompted")
                else:
                    print("\n[✓] Token has the correct scopes!")

            else:
                print("\n[!] Could not decode token (may not be a JWT)")
        else:
            print("\n[!] No access_token found in credential")

        # Check refresh token
        refresh_token = cred_data.get("refresh_token", "")
        print("\n[Refresh Token]")
        print(f"  Present: {'Yes' if refresh_token else 'No'}")
        print(f"  Length: {len(refresh_token) if refresh_token else 0}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
