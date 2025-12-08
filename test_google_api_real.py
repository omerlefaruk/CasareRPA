"""
Test Google API integration with real credentials.

This script tests:
1. Gmail API - List emails
2. Google Sheets API - List spreadsheets
3. Google Drive API - List files
4. Google Calendar API - List calendars
5. Google Docs API - List documents
"""

import asyncio
from datetime import datetime, timedelta

# Google API client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from casare_rpa.infrastructure.security.credential_store import get_credential_store
from casare_rpa.infrastructure.security.google_oauth import get_google_access_token


def get_service(service_name: str, version: str, access_token: str, scopes: list):
    """Create a Google API service using access token."""
    credentials = Credentials(token=access_token, scopes=scopes)
    return build(service_name, version, credentials=credentials)


async def test_gmail_api(credential_id: str, scopes: list):
    """Test Gmail API."""
    print("\n" + "=" * 50)
    print("Testing Gmail API")
    print("=" * 50)

    # Check if we have Gmail scope
    gmail_scopes = [s for s in scopes if "gmail" in s.lower()]
    if not gmail_scopes:
        print("  SKIPPED: No Gmail scope granted")
        return None

    try:
        access_token = await get_google_access_token(credential_id)
        service = get_service("gmail", "v1", access_token, scopes)

        # List first 5 emails
        results = service.users().messages().list(userId="me", maxResults=5).execute()

        messages = results.get("messages", [])
        print(f"  Found {len(messages)} recent emails")

        if messages:
            # Get details of first email
            msg = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=messages[0]["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From"],
                )
                .execute()
            )

            headers = {
                h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
            }
            print(f"  Latest email subject: {headers.get('Subject', 'N/A')[:50]}...")
            print(f"  From: {headers.get('From', 'N/A')[:50]}")

        print("  Gmail API: OK")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_sheets_api(credential_id: str, scopes: list):
    """Test Google Sheets API."""
    print("\n" + "=" * 50)
    print("Testing Google Sheets API")
    print("=" * 50)

    # Check if we have Sheets or Drive scope
    sheets_scopes = [
        s for s in scopes if "spreadsheets" in s.lower() or "drive" in s.lower()
    ]
    if not sheets_scopes:
        print("  SKIPPED: No Sheets/Drive scope granted")
        return None

    try:
        access_token = await get_google_access_token(credential_id)

        # First get Drive service to list spreadsheets
        drive_service = get_service("drive", "v3", access_token, scopes)

        # List spreadsheets
        results = (
            drive_service.files()
            .list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                pageSize=5,
                fields="files(id, name)",
            )
            .execute()
        )

        files = results.get("files", [])
        print(f"  Found {len(files)} spreadsheets")

        for f in files[:3]:
            print(f"  - {f['name'][:40]}...")

        # If we have a spreadsheet, try to read it
        if files:
            sheets_service = get_service("sheets", "v4", access_token, scopes)
            spreadsheet_id = files[0]["id"]
            try:
                spreadsheet = (
                    sheets_service.spreadsheets()
                    .get(spreadsheetId=spreadsheet_id)
                    .execute()
                )

                sheet_count = len(spreadsheet.get("sheets", []))
                print(f"  First spreadsheet has {sheet_count} sheets")
            except Exception as e:
                print(f"  Warning: Could not read spreadsheet details: {e}")

        print("  Sheets API: OK")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_drive_api(credential_id: str, scopes: list):
    """Test Google Drive API."""
    print("\n" + "=" * 50)
    print("Testing Google Drive API")
    print("=" * 50)

    # Check if we have Drive scope
    drive_scopes = [s for s in scopes if "drive" in s.lower()]
    if not drive_scopes:
        print("  SKIPPED: No Drive scope granted")
        return None

    try:
        access_token = await get_google_access_token(credential_id)
        service = get_service("drive", "v3", access_token, scopes)

        # List recent files
        results = (
            service.files()
            .list(
                pageSize=10,
                fields="files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        files = results.get("files", [])
        print(f"  Found {len(files)} recent files")

        for f in files[:5]:
            mime = f.get("mimeType", "unknown").split(".")[-1]
            name = f["name"][:35].encode("ascii", "replace").decode("ascii")
            print(f"  - {name:<35} ({mime})")

        # Get storage quota
        try:
            about = service.about().get(fields="storageQuota").execute()
            quota = about.get("storageQuota", {})
            used_gb = int(quota.get("usage", 0)) / (1024**3)
            limit_gb = int(quota.get("limit", 0)) / (1024**3)
            if limit_gb > 0:
                print(f"  Storage: {used_gb:.2f} GB / {limit_gb:.2f} GB")
        except Exception:
            pass

        print("  Drive API: OK")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_calendar_api(credential_id: str, scopes: list):
    """Test Google Calendar API."""
    print("\n" + "=" * 50)
    print("Testing Google Calendar API")
    print("=" * 50)

    # Check if we have Calendar scope
    calendar_scopes = [s for s in scopes if "calendar" in s.lower()]
    if not calendar_scopes:
        print("  SKIPPED: No Calendar scope granted")
        return None

    try:
        access_token = await get_google_access_token(credential_id)
        service = get_service("calendar", "v3", access_token, scopes)

        # List calendars
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        print(f"  Found {len(calendars)} calendars")

        for cal in calendars[:3]:
            primary = " (primary)" if cal.get("primary") else ""
            print(f"  - {cal.get('summary', 'Unnamed')[:40]}{primary}")

        # Get upcoming events
        now = datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=3,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        if events:
            print("  Upcoming events:")
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(f"  - {start[:10]}: {event.get('summary', 'No title')[:30]}")
        else:
            print("  No upcoming events")

        print("  Calendar API: OK")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_docs_api(credential_id: str, scopes: list):
    """Test Google Docs API."""
    print("\n" + "=" * 50)
    print("Testing Google Docs API")
    print("=" * 50)

    # Check if we have Docs or Drive scope
    docs_scopes = [s for s in scopes if "document" in s.lower() or "drive" in s.lower()]
    if not docs_scopes:
        print("  SKIPPED: No Docs/Drive scope granted")
        return None

    try:
        access_token = await get_google_access_token(credential_id)

        # First get Drive service to list docs
        drive_service = get_service("drive", "v3", access_token, scopes)

        # List documents
        results = (
            drive_service.files()
            .list(
                q="mimeType='application/vnd.google-apps.document'",
                pageSize=5,
                fields="files(id, name)",
            )
            .execute()
        )

        files = results.get("files", [])
        print(f"  Found {len(files)} documents")

        for f in files[:3]:
            name = f["name"][:40].encode("ascii", "replace").decode("ascii")
            print(f"  - {name}...")

        # If we have a document, try to read it
        if files:
            docs_service = get_service("docs", "v1", access_token, scopes)
            doc_id = files[0]["id"]
            try:
                document = docs_service.documents().get(documentId=doc_id).execute()

                title = document.get("title", "Untitled")[:40]
                title = title.encode("ascii", "replace").decode("ascii")
                print(f"  First document title: {title}")
            except Exception as e:
                print(f"  Warning: Could not read document details: {e}")

        print("  Docs API: OK")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print(" Google API Integration Test - Real Credentials")
    print("=" * 60)

    # Get credential store
    store = get_credential_store()

    # List Google credentials
    google_creds = store.list_google_credentials()

    if not google_creds:
        print("\nERROR: No Google credentials found!")
        print("Please add a Google account in the Credential Manager first.")
        print("  1. Run the CasareRPA app")
        print("  2. Go to Edit > Credentials")
        print("  3. Click 'Add Google Account' in the Google tab")
        return

    print(f"\nFound {len(google_creds)} Google credential(s):")
    for cred in google_creds:
        print(f"  - {cred['name']} (ID: {cred['id'][:20]}...)")

    # Use first credential
    credential_id = google_creds[0]["id"]
    cred_data = store.get_credential(credential_id)

    if not cred_data:
        print("\nERROR: Could not retrieve credential data!")
        return

    user_email = cred_data.get("user_email", "Unknown")
    scopes = cred_data.get("scopes", [])

    print(f"\nUsing credential: {google_creds[0]['name']}")
    print(f"User email: {user_email}")
    print(f"Scopes granted ({len(scopes)}):")
    for scope in scopes:
        print(f"  - {scope.split('/')[-1]}")

    # Run tests
    results = {}

    print("\nRunning API tests...")

    results["Gmail"] = await test_gmail_api(credential_id, scopes)
    results["Sheets"] = await test_sheets_api(credential_id, scopes)
    results["Drive"] = await test_drive_api(credential_id, scopes)
    results["Calendar"] = await test_calendar_api(credential_id, scopes)
    results["Docs"] = await test_docs_api(credential_id, scopes)

    # Summary
    print("\n" + "=" * 60)
    print(" Test Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for api, success in results.items():
        if success is None:
            status = "SKIP"
            skipped += 1
        elif success:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        print(f"  {api:20} [{status}]")

    print("-" * 40)
    print(f"  Passed: {passed}, Failed: {failed}, Skipped: {skipped}")

    if failed == 0 and passed > 0:
        print("\n  All active API tests PASSED!")
    elif failed > 0:
        print(f"\n  {failed} test(s) failed - check scopes or permissions")
    else:
        print("\n  No tests could run - check your scopes")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
