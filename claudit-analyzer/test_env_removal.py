#!/usr/bin/env python3
"""Test environment variable removal"""

import subprocess
import os

print(f"Current GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# Method from the script
clean_env = {}
for key, value in os.environ.items():
    if key != "GOOGLE_APPLICATION_CREDENTIALS":
        clean_env[key] = value

print(f"\nClean env has {len(clean_env)} vars")
print(f"GOOGLE_APPLICATION_CREDENTIALS in clean_env: {'GOOGLE_APPLICATION_CREDENTIALS' in clean_env}")

# Test with echo
result = subprocess.run(
    ["bash", "-c", "echo GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"],
    env=clean_env,
    capture_output=True,
    text=True
)
print(f"\nSubprocess sees: {result.stdout.strip()}")

# Test gemini with tiny input
print("\nTesting gemini with clean env...")
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input="Say hello",
        capture_output=True,
        text=True,
        env=clean_env,
        timeout=10
    )
    print(f"Success! Output: {result.stdout.strip()}")
except subprocess.TimeoutExpired:
    print("TIMEOUT - still hanging!")
    # Let's see what's in stderr
    result = subprocess.run(
        ["timeout", "5", "gemini", "-m", "gemini-2.5-flash"],
        input="Say hello",
        capture_output=True,
        text=True,
        env=clean_env
    )
    print(f"Exit code: {result.returncode}")
    print(f"Stderr: {result.stderr}")
except Exception as e:
    print(f"Error: {e}")