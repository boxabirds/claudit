#!/usr/bin/env python3
"""Test what gemini CLI is actually doing"""

import subprocess
import os
import time

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

test_input = "Say hello and nothing else"

print("Running gemini with debug flag...")
start_time = time.time()

process = subprocess.Popen(
    ["gemini", "-m", "gemini-2.5-flash", "-d"],  # -d for debug
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)

# Send input and see what happens
stdout, stderr = process.communicate(input=test_input, timeout=30)

elapsed = time.time() - start_time
print(f"\nCompleted in {elapsed:.1f} seconds")
print(f"Exit code: {process.returncode}")
print(f"\nStdout:\n{stdout}")
print(f"\nStderr:\n{stderr}")