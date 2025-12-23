#!/usr/bin/env python3
"""
Generate secure API tokens for robot authentication.

Creates cryptographically secure tokens and their SHA-256 hashes for
storing in ROBOT_TOKENS environment variable.

Usage:
    python tools/generate_robot_token.py robot-001
    python tools/generate_robot_token.py robot-002 robot-003 robot-004
"""

import hashlib
import secrets
import sys


def generate_robot_token(robot_id: str) -> tuple[str, str]:
    """
    Generate secure API token for robot.

    Args:
        robot_id: Unique identifier for robot (e.g., "robot-001")

    Returns:
        Tuple of (raw_token, token_hash)
    """
    # Generate 32-byte (256-bit) cryptographically secure token
    # Base64-encoded = 43 characters
    token = secrets.token_urlsafe(32)

    # SHA-256 hash for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash


def main():
    """Generate tokens for specified robot IDs."""
    if len(sys.argv) < 2:
        print("Usage: python generate_robot_token.py robot-001 [robot-002 ...]")
        print("\nExample:")
        print("  python tools/generate_robot_token.py robot-001")
        print("  python tools/generate_robot_token.py robot-001 robot-002 robot-003")
        sys.exit(1)

    robot_ids = sys.argv[1:]

    print("=" * 80)
    print("Robot API Token Generator")
    print("=" * 80)
    print()

    env_entries = []

    for robot_id in robot_ids:
        token, token_hash = generate_robot_token(robot_id)

        print(f"Robot ID: {robot_id}")
        print(f"  Raw Token:  {token}")
        print(f"  Token Hash: {token_hash}")
        print()
        print(f"  Robot Config ({robot_id}):")
        print("    Add to config/robot.yaml on robot PC:")
        print("    orchestrator:")
        print(f'      api_token: "{token}"')
        print()

        env_entries.append(f"{robot_id}:{token_hash}")

    print("-" * 80)
    print("Orchestrator Environment Variable:")
    print("-" * 80)
    print()
    print("Add to orchestrator .env file or environment:")
    print()
    print("ROBOT_AUTH_ENABLED=true")
    print(f'ROBOT_TOKENS="{",".join(env_entries)}"')
    print()
    print("=" * 80)
    print()
    print("⚠️  SECURITY WARNING:")
    print("  - Store raw tokens SECURELY on robot PCs only")
    print("  - Never commit tokens to version control")
    print("  - Only store token HASHES in orchestrator environment")
    print("  - Rotate tokens if compromised")
    print("=" * 80)


if __name__ == "__main__":
    main()
