#!/usr/bin/env python3
"""Test gemini with simple input to isolate the issue"""

import subprocess
import os

# Test 1: Very simple input
print("=== Test 1: Simple input ===")
simple_input = "Say hello and nothing else"

env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

cmd = ["gemini", "-m", "gemini-2.5-flash"]

try:
    result = subprocess.run(
        cmd,
        input=simple_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=10
    )
    print(f"Success! Output: {result.stdout.strip()}")
except subprocess.TimeoutExpired:
    print("TIMEOUT - even simple input hangs!")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Check what happens with no env at all
print("\n=== Test 2: No env dict ===")
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=simple_input,
        capture_output=True,
        text=True,
        env={},  # Empty environment
        timeout=10
    )
    print(f"Success! Output: {result.stdout.strip()}")
except subprocess.TimeoutExpired:
    print("TIMEOUT with empty env!")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Shell approach
print("\n=== Test 3: Shell approach ===")
try:
    result = subprocess.run(
        "unset GOOGLE_APPLICATION_CREDENTIALS && echo 'Say hello' | gemini -m gemini-2.5-flash",
        shell=True,
        capture_output=True,
        text=True,
        timeout=10
    )
    print(f"Success! Output: {result.stdout.strip()}")
except subprocess.TimeoutExpired:
    print("TIMEOUT with shell!")
except Exception as e:
    print(f"Error: {e}")