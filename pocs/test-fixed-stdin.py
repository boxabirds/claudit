#!/usr/bin/env python3
"""Test the corrected gemini CLI usage"""

import subprocess
import os

# Remove Google credentials for testing
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("Removed GOOGLE_APPLICATION_CREDENTIALS from environment")

prompt = "What is 2+2? Reply with just the number."

print("=== Testing corrected approach: gemini (no -p flag) ===")
print(f"Command: gemini -m gemini-2.5-flash")
print(f"Sending via stdin: {prompt}")
print()

try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=15,
        env=env
    )
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr[:500]}")
    else:
        print("No stderr")
        
except subprocess.TimeoutExpired:
    print("TIMEOUT - still hanging!")
except Exception as e:
    print(f"Error: {e}")

print("\nThis should work now since we're not using the incorrect -p - syntax")