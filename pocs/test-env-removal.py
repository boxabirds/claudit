#!/usr/bin/env python3
"""
Test if environment variable removal is working
"""

import subprocess
import os

print("Original environment:")
print(f"  GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')}")

# Test 1: Direct subprocess with full environment
print("\n=== Test 1: subprocess.run with full env ===")
result = subprocess.run(
    ["./gemini-debug-wrapper.sh", "-m", "gemini-2.5-flash"],
    input="Say TEST1",
    capture_output=True,
    text=True,
    timeout=10
)
print("Exit code:", result.returncode)
print("Stderr preview:", result.stderr.split('\n')[7] if result.stderr else "none")  # Line with GOOGLE_APPLICATION_CREDENTIALS

# Test 2: With env.copy() and del
print("\n=== Test 2: env.copy() and del ===")
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("Deleted GOOGLE_APPLICATION_CREDENTIALS from copy")
print(f"In copied env: {'GOOGLE_APPLICATION_CREDENTIALS' in env}")

result = subprocess.run(
    ["./gemini-debug-wrapper.sh", "-m", "gemini-2.5-flash"],
    input="Say TEST2",
    capture_output=True,
    text=True,
    env=env,
    timeout=10
)
print("Exit code:", result.returncode)
print("Stderr preview:", result.stderr.split('\n')[7] if result.stderr else "none")  # Line with GOOGLE_APPLICATION_CREDENTIALS

# Test 3: With explicit None
print("\n=== Test 3: Set to empty string ===")
env = os.environ.copy()
env["GOOGLE_APPLICATION_CREDENTIALS"] = ""

result = subprocess.run(
    ["./gemini-debug-wrapper.sh", "-m", "gemini-2.5-flash"],
    input="Say TEST3",
    capture_output=True,
    text=True,
    env=env,
    timeout=10
)
print("Exit code:", result.returncode)
print("Stderr preview:", result.stderr.split('\n')[7] if result.stderr else "none")  # Line with GOOGLE_APPLICATION_CREDENTIALS