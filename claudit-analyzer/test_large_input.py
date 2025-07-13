#!/usr/bin/env python3
"""Test with large input like the script uses"""

import subprocess
import os
import time

# Create clean env
clean_env = {}
for key, value in os.environ.items():
    if key != "GOOGLE_APPLICATION_CREDENTIALS":
        clean_env[key] = value

# Test with exact size from script (1MB)
print("Creating 1MB input...")
large_input = "x" * 1030368  # Same size as script

print(f"Testing gemini with {len(large_input)} chars...")
start = time.time()

try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=large_input,
        capture_output=True,
        text=True,
        env=clean_env,
        timeout=120
    )
    elapsed = time.time() - start
    print(f"Success in {elapsed:.1f}s!")
    print(f"Output length: {len(result.stdout)}")
except subprocess.TimeoutExpired:
    elapsed = time.time() - start
    print(f"TIMEOUT after {elapsed:.1f}s")
    print("This confirms the issue is with large inputs")
    
    # Try to get more info
    print("\nTrying with strace to see what's happening...")
    result = subprocess.run(
        ["timeout", "10", "strace", "-e", "trace=read,write", "gemini", "-m", "gemini-2.5-flash"],
        input="test",
        capture_output=True,
        text=True,
        env=clean_env
    )
    print("Strace output (last 20 lines):")
    print('\n'.join(result.stderr.splitlines()[-20:]))