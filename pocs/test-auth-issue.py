#!/usr/bin/env python3
"""
Test if the timeout is due to auth issues
"""

import subprocess
import os

# Test 1: With original environment
print("=== Test 1: With GOOGLE_APPLICATION_CREDENTIALS ===")
result = subprocess.run(
    ["gemini", "-m", "gemini-2.5-flash"],
    input="Say OK",
    capture_output=True,
    text=True,
    timeout=5
)
print(f"Exit code: {result.returncode}")
print(f"Output: {result.stdout}")
if result.stderr:
    print(f"Stderr: {result.stderr[:200]}")

# Test 2: Without GOOGLE_APPLICATION_CREDENTIALS
print("\n=== Test 2: Without GOOGLE_APPLICATION_CREDENTIALS ===")
env = os.environ.copy()
if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
    del env['GOOGLE_APPLICATION_CREDENTIALS']
    
result = subprocess.run(
    ["gemini", "-m", "gemini-2.5-flash"],
    input="Say OK", 
    capture_output=True,
    text=True,
    env=env,
    timeout=5
)
print(f"Exit code: {result.returncode}")
print(f"Output: {result.stdout}")
if result.stderr:
    print(f"Stderr: {result.stderr[:200]}")

# Test 3: Check .gemini directory
print("\n=== Gemini Config ===")
gemini_dir = os.path.expanduser("~/.gemini")
if os.path.exists(gemini_dir):
    print(f"✓ {gemini_dir} exists")
    for file in os.listdir(gemini_dir):
        path = os.path.join(gemini_dir, file)
        stat = os.stat(path)
        print(f"  {file}: {stat.st_size} bytes, modified {stat.st_mtime}")
else:
    print(f"✗ {gemini_dir} not found")