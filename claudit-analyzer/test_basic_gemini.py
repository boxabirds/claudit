#!/usr/bin/env python3
"""Most basic gemini test"""

import subprocess
import os

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("Removed GOOGLE_APPLICATION_CREDENTIALS")

print("Test 1: Direct command line")
# First test if gemini works at all from command line
result = os.system('unset GOOGLE_APPLICATION_CREDENTIALS && echo "hi" | gemini -m gemini-2.5-flash')
print(f"Direct command line result: {result}")

print("\nTest 2: subprocess.run with shell=True")
result = subprocess.run(
    'unset GOOGLE_APPLICATION_CREDENTIALS && echo "hi" | gemini -m gemini-2.5-flash',
    shell=True,
    capture_output=True,
    text=True
)
print(f"Shell result: {result.returncode}")
print(f"Output: {result.stdout[:100]}")

print("\nTest 3: subprocess.run without shell")
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input="hi",
        capture_output=True,
        text=True,
        env=env,
        timeout=10
    )
    print(f"Success! Exit code: {result.returncode}")
    print(f"Output: {result.stdout[:100]}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
except Exception as e:
    print(f"Error: {e}")