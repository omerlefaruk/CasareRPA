import os
import sys


def check_env():
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        return

    # Check file size
    size = os.path.getsize(".env")
    print(f"File size: {size} bytes")

    # Try reading as UTF-8
    try:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        print("✅ Successfully read as UTF-8")
        print("--- Content Preview (first 500 chars) ---")
        print(content[:500])
        print("--- End Preview ---")

        # Check for specific variables
        if "API_SECRET" in content:
            print("Found API_SECRET")
        else:
            print("❌ API_SECRET not found in text")

    except UnicodeDecodeError:
        print("❌ Failed to read as UTF-8. Checking other encodings...")
        try:
            with open(".env", "r", encoding="utf-16") as f:
                content = f.read()
            print("⚠️ File appears to be UTF-16 encoded!")
        except Exception as e:
            print(f"❌ Failed to decode: {e}")


if __name__ == "__main__":
    check_env()
