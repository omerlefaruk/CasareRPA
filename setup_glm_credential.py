"""
Script to add GLM (Z.ai) API key credential.
Run this once to store your GLM API key securely.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    from casare_rpa.infrastructure.security.credential_store import (
        get_credential_store,
        CredentialType,
    )

    print("=" * 60)
    print("GLM (Z.ai) API Key Setup")
    print("=" * 60)
    print()
    print("This will store your GLM API key securely in the credential store.")
    print("The key is encrypted and only accessible on this machine.")
    print()

    # Get API key from user
    api_key = input("Enter your GLM API key (format: id.secret): ").strip()

    if not api_key:
        print("Error: API key cannot be empty!")
        return

    if "." not in api_key:
        print("Warning: GLM API keys usually have format 'id.secret'")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != "y":
            return

    # Get name for the credential
    name = input("Enter a name for this credential (default: GLM API Key): ").strip()
    if not name:
        name = "GLM API Key"

    # Store the credential
    store = get_credential_store()

    cred_id = store.save_credential(
        name=name,
        credential_type=CredentialType.API_KEY_KIND,
        category="llm",
        data={
            "api_key": api_key,
            "provider": "glm",
        },
        description="GLM (Z.ai) API key for AI-powered CAPTCHA solving and LLM tasks",
        tags=["glm", "ai", "vision"],
    )

    print()
    print("=" * 60)
    print(f"✓ GLM credential saved successfully!")
    print(f"  Credential ID: {cred_id}")
    print(f"  Name: {name}")
    print("=" * 60)
    print()
    print("You can now use this credential in:")
    print("  - Solve CAPTCHA (AI) node")
    print("  - LLM/AI nodes with GLM provider")
    print()


if __name__ == "__main__":
    main()
