"""
Helper script to update database credentials in .env file
"""

import os
import re


def update_credentials():
    print("=" * 60)
    print(" CasareRPA Database Credentials Updater")
    print("=" * 60)
    print()
    print("Please provide the new database connection string from Supabase.")
    print("Format should be:")
    print(
        "postgresql://postgres.PROJECT:PASSWORD@REGION.pooler.supabase.com:PORT/postgres"
    )
    print()

    # Get new connection string
    new_url = input("Enter the new POSTGRES_URL (port 6543): ").strip()

    if not new_url.startswith("postgresql://"):
        print("❌ Invalid connection string format!")
        return

    # Derive DATABASE_URL (port 5432) from POSTGRES_URL
    database_url = new_url.replace(":6543/", ":5432/")

    print()
    print("URLs to be set:")
    print(f"POSTGRES_URL: {new_url[:50]}...{new_url[-20:]}")
    print(f"DATABASE_URL: {database_url[:50]}...{database_url[-20:]}")
    print()

    confirm = input("Update .env file? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    # Read current .env
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    # Update POSTGRES_URL
    if "POSTGRES_URL=" in content:
        content = re.sub(r"POSTGRES_URL=.*", f"POSTGRES_URL={new_url}", content)
    else:
        content += f"\nPOSTGRES_URL={new_url}\n"

    # Update DATABASE_URL
    if "DATABASE_URL=" in content:
        content = re.sub(r"DATABASE_URL=.*", f"DATABASE_URL={database_url}", content)
    else:
        content += f"DATABASE_URL={database_url}\n"

    # Write back
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

    print()
    print("✅ .env file updated successfully!")
    print()
    print("Next steps:")
    print("1. Restart the application: launch.bat")
    print("2. Test connection: python tests/e2e/test_full_execution.py")


if __name__ == "__main__":
    try:
        update_credentials()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
