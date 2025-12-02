#!/usr/bin/env python3
"""
CasareRPA Setup via Supabase REST API.

Uses REST API instead of direct PostgreSQL connection (works without IPv6).

Usage:
    python deploy/setup_via_rest.py
"""

import asyncio
import hashlib
import os
import secrets
import socket
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx

# Supabase configuration
SUPABASE_URL = "https://znaauaswqmurwfglantv.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpuYWF1YXN3cW11cndmZ2xhbnR2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM5ODIwODksImV4cCI6MjA3OTU1ODA4OX0.np-UjI33_tqgcU6_MOOoT5o3J3pg19AP3UhwCeI3Kxs"


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


async def check_tables():
    """Check what tables exist via REST API."""
    async with httpx.AsyncClient() as client:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        }

        # Get API schema to see available tables
        resp = await client.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            paths = list(data.get("paths", {}).keys())
            tables = [p.strip("/") for p in paths if p != "/"]
            return tables
        return []


async def get_robots():
    """Get existing robots."""
    async with httpx.AsyncClient() as client:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        }

        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/robots?select=*",
            headers=headers,
        )

        if resp.status_code == 200:
            return resp.json()
        return []


async def create_robot(name: str, hostname: str):
    """Create a new robot via REST API."""
    async with httpx.AsyncClient() as client:
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        data = {
            "name": name,
            "status": "offline",
            "version": "3.0.0",
            "metrics": {
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0,
            },
        }

        resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/robots",
            headers=headers,
            json=data,
        )

        if resp.status_code == 201:
            return resp.json()[0] if resp.json() else None
        elif resp.status_code == 409:
            # Already exists, fetch it
            resp2 = await client.get(
                f"{SUPABASE_URL}/rest/v1/robots?name=eq.{name}",
                headers=headers,
            )
            if resp2.status_code == 200 and resp2.json():
                return resp2.json()[0]

        print(f"  Error creating robot: {resp.status_code} - {resp.text}")
        return None


async def main():
    print_header("CasareRPA Setup (REST API)")

    print("\nChecking Supabase connection...")
    tables = await check_tables()

    if tables:
        print("  [OK] Connected to Supabase")
        print(
            f"  Tables found: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}"
        )
    else:
        print("  [FAIL] Could not connect to Supabase")
        return

    print_header("Existing Robots")
    robots = await get_robots()

    if robots:
        print(f"  Found {len(robots)} robot(s):")
        for r in robots:
            print(
                f"    - {r.get('name')}: {r.get('status')} (ID: {r.get('id')[:8]}...)"
            )
    else:
        print("  No robots found.")

    # Create new robot
    print_header("Create Robot")

    robot_name = f"Robot-{socket.gethostname()}"
    print(f"  Creating robot: {robot_name}")

    robot = await create_robot(robot_name, socket.gethostname())

    if robot:
        print(f"  [OK] Robot ID: {robot.get('id')}")
    else:
        print("  [WARN] Could not create robot (may already exist)")

    # Generate API key (for reference - actual key storage needs direct DB access or edge function)
    print_header("API Key")

    token = secrets.token_urlsafe(32)
    api_key = f"crpa_{token}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    print("\n  Generated API Key (save this!):")
    print(f"  {api_key}")
    print("\n  Hash (for verification):")
    print(f"  {key_hash[:16]}...")

    print("\n  NOTE: To store API key in database, you need:")
    print("  1. Get Connection Pooler URL from Supabase Dashboard")
    print("  2. Update .env with correct pooler URL")
    print("  3. Or use Supabase Edge Function to create keys")

    # Summary
    print_header("Summary")

    print(f"""
  Supabase REST API: Working
  Tables: {', '.join(tables[:3])}...
  Robots: {len(robots)} existing

  Your robot can use the REST API at:
    {SUPABASE_URL}/rest/v1/

  To complete setup with direct PostgreSQL:
    1. Go to: https://supabase.com/dashboard/project/znaauaswqmurwfglantv/settings/database
    2. Find "Connection Pooling" section
    3. Copy the connection string
    4. Update .env with the correct pooler URL
    5. Run: python deploy/auto_setup.py setup
""")


if __name__ == "__main__":
    asyncio.run(main())
