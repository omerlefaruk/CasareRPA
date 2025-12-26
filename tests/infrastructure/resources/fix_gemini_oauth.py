"""
Helper to fix Gemini OAuth by deleting and re-authenticating the credential.

This script will:
1. Check current credential scopes
2. Delete the existing Google credential
3. Provide instructions to re-authenticate

Run with: python tests/infrastructure/resources/fix_gemini_oauth.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


async def main():
    from casare_rpa.infrastructure.security.credential_store import get_credential_store

    print("\n" + "=" * 70)
    print("GEMINI OAUTH FIX HELPER")
    print("=" * 70)

    store = get_credential_store()

    # Find Google OAuth credentials
    credentials = store.list_credentials()
    google_creds = [
        c for c in credentials if c.get("type") == "google_oauth" or c.get("category") == "google"
    ]

    if not google_creds:
        print("\n[!] No Google OAuth credentials found.")
        print("    You're good to go! Please add a new credential via Canvas.")
        return

    print(f"\n[1] Found {len(google_creds)} Google credential(s):")
    for cred in google_creds:
        cred_id = cred["id"]
        print(f"\n    Name: {cred.get('name')}")
        print(f"    ID: {cred_id}")
        print(f"    Type: {cred.get('type')}")

        # Check scopes
        cred_data = store.get_credential(cred_id)
        if cred_data:
            scopes = cred_data.get("scopes", [])
            print(f"    Scopes ({len(scopes)}):")
            for scope in scopes:
                print(f"      - {scope}")

            has_gen = any("generative-language" in s for s in scopes)
            has_cloud = any("cloud-platform" in s for s in scopes)

            print("\n    Scope Check:")
            print(f"      generative-language: {'[OK]' if has_gen else '[MISSING]'}")
            print(f"      cloud-platform: {'[OK]' if has_cloud else '[MISSING]'}")

            if not has_gen:
                print("\n    [!] This credential needs to be re-created!")
                print("        Missing: generative-language scope")
                print("        (for Gemini AI Studio - no GCP billing needed)")

    print("\n" + "=" * 70)
    print("\n[ACTION REQUIRED]")
    print("\nYour Google OAuth credential was created with old scopes.")
    print("To fix this, you need to delete and re-authenticate:\n")
    print("1. Open CasareRPA Canvas")
    print("2. Go to Settings -> Credentials")
    print("3. Delete your existing 'Gemini AI Studio' credential")
    print("4. Click 'Connect Gemini AI Studio'")
    print("5. Approve the OAuth permission (only generative-language scope)\n")
    print("Note: This only requires a Gemini subscription, not GCP billing.")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
