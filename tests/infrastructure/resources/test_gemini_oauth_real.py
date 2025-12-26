"""
Real integration test for Gemini AI Studio OAuth.

This test uses the actual stored credential to verify OAuth works end-to-end.
Run with: python tests/infrastructure/resources/test_gemini_oauth_real.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


async def test_gemini_oauth_real():
    """Test Gemini OAuth with real credential."""
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMConfig,
        LLMProvider,
        LLMResourceManager,
    )
    from casare_rpa.infrastructure.security.credential_store import get_credential_store
    from casare_rpa.infrastructure.security.gemini_oauth import GEMINI_SCOPES, get_gemini_manager

    print("\n" + "=" * 60)
    print("GEMINI AI STUDIO OAUTH TEST")
    print("=" * 60)

    # Step 1: Find Google OAuth credentials
    print("\n[1] Looking for Google OAuth credentials...")
    store = get_credential_store()
    credentials = store.list_credentials()

    google_creds = [
        c for c in credentials if c.get("type") == "google_oauth" or c.get("category") == "google"
    ]

    if not google_creds:
        print("  [X] No Google OAuth credentials found!")
        print("  Please create one via: Canvas -> Settings -> Connect Gemini AI Studio")
        return False

    print(f"  [OK] Found {len(google_creds)} Google credential(s):")
    for cred in google_creds:
        print(f"    - {cred.get('name')} (ID: {cred.get('id')})")
        print(f"      Type: {cred.get('type')}, Category: {cred.get('category')}")
        print(f"      Tags: {cred.get('tags', [])}")

    # Use the first Google credential
    test_cred = google_creds[0]
    cred_id = test_cred["id"]
    print(f"\n[2] Testing with credential: {test_cred['name']}")

    # Step 2: Test OAuth token retrieval
    print("\n[3] Retrieving OAuth token...")
    try:
        manager = await get_gemini_manager()
        access_token = await manager.get_access_token(cred_id)
        print(f"  [OK] Token retrieved (length: {len(access_token)} chars)")
        print(f"  Token preview: {access_token[:20]}...{access_token[-20:]}")
    except Exception as e:
        print(f"  [X] Failed to retrieve token: {e}")
        return False

    # Step 3: Check OAuth scopes
    print("\n[4] OAuth scopes being requested:")
    for scope in GEMINI_SCOPES:
        print(f"  - {scope}")

    # Step 4: Check actual scopes in the credential
    print("\n[5] Checking actual scopes in stored credential...")
    cred_data = store.get_credential(cred_id)
    if cred_data:
        actual_scopes = cred_data.get("scopes", [])
        print(f"  Stored scopes ({len(actual_scopes)}):")
        for scope in actual_scopes:
            print(f"    - {scope}")

        has_cloud = any("cloud-platform" in s for s in actual_scopes)
        has_gen = any("generative-language" in s for s in actual_scopes)

        print("\n  Scope Analysis:")
        print(f"    cloud-platform: {'[OK]' if has_cloud else '[X]'}")
        print(f"    generative-language: {'[OK]' if has_gen else '[X]'}")

        if not (has_cloud or has_gen):
            print("\n  [X] Token has neither scope!")
            return False
    else:
        print("  [X] Could not read credential data")
        return False

    # Step 5: Test direct API call
    # Try Gemini AI Studio API first (with cloud-platform scope)
    print("\n[6] Testing Gemini AI Studio API...")
    endpoint = "generativelanguage.googleapis.com/v1beta"

    import aiohttp

    model_name = "gemini-2.0-flash-exp"

    url = f"https://{endpoint}/models/{model_name}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Hello! Please respond with 'SUCCESS' if you can read this."}],
            }
        ],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 50},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("  [OK] API call successful!")
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"  Response: {text[:100]}")

                    usage = result.get("usageMetadata", {})
                    print(f"  Tokens used: {usage.get('totalTokenCount', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"  [X] API call failed with status {response.status}")
                    print(f"  Error: {error_text[:500]}")

                    if (
                        "scope" in error_text.lower()
                        or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in error_text
                    ):
                        print(
                            "\n  [!] SCOPE ERROR - Token doesn't have required scope for this endpoint"
                        )
                    return False
    except Exception as e:
        print(f"  [X] API call exception: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 7: Test via LLMResourceManager
    print("\n[7] Testing via LLMResourceManager...")
    try:
        llm_manager = LLMResourceManager()
        config = LLMConfig(
            provider=LLMProvider.CUSTOM,
            model=f"models/{model_name}",
            credential_id=cred_id,
        )
        llm_manager.configure(config)

        response = await llm_manager.completion(
            prompt="Say 'TEST SUCCESS' if this works.",
            temperature=0.7,
            max_tokens=50,
        )
        print("  [OK] LLMResourceManager successful!")
        print(f"  Response: {response.content[:100]}")
        print(f"  Tokens: {response.total_tokens}")
    except Exception as e:
        print(f"  [X] LLMResourceManager failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_gemini_oauth_real())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"\n[X] Test failed with exception: {e}")
        sys.exit(1)
