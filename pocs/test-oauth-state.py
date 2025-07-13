#!/usr/bin/env python3
"""
Check gemini CLI OAuth state
"""

import os
import subprocess
import json
from pathlib import Path

print("=== Gemini CLI Auth State ===\n")

# Check OAuth file
oauth_file = Path.home() / ".gemini/oauth_creds.json"
if oauth_file.exists():
    print(f"✓ OAuth file exists: {oauth_file}")
    print(f"  Size: {oauth_file.stat().st_size} bytes")
    print(f"  Modified: {oauth_file.stat().st_mtime}")
else:
    print(f"✗ OAuth file missing: {oauth_file}")

# Check GOOGLE_APPLICATION_CREDENTIALS
gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if gac:
    print(f"\n⚠️  GOOGLE_APPLICATION_CREDENTIALS is set: {gac}")
else:
    print(f"\n✓ GOOGLE_APPLICATION_CREDENTIALS not set")

# Test 1: With GOOGLE_APPLICATION_CREDENTIALS (should fail)
if gac:
    print("\n=== Test 1: With GOOGLE_APPLICATION_CREDENTIALS ===")
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input="Say 'OK'",
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Stderr: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT - likely waiting for auth")

# Test 2: Without GOOGLE_APPLICATION_CREDENTIALS (should work)
print("\n=== Test 2: Without GOOGLE_APPLICATION_CREDENTIALS ===")
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input="Say 'OK'",
        capture_output=True,
        text=True,
        timeout=5,
        env=env
    )
    print(f"Exit code: {result.returncode}")
    print(f"Output: {result.stdout.strip()}")
    if result.stderr:
        print(f"Stderr: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("✗ TIMEOUT - OAuth might need refresh")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Check if we can read OAuth creds
if oauth_file.exists():
    print(f"\n=== OAuth Creds Info ===")
    try:
        with open(oauth_file, 'r') as f:
            creds = json.load(f)
            print(f"✓ OAuth creds are valid JSON")
            if 'expiry' in creds:
                print(f"  Expiry: {creds['expiry']}")
    except Exception as e:
        print(f"✗ Could not read OAuth creds: {e}")