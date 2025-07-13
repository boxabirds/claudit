#!/usr/bin/env python3
"""Test with the actual content that's failing"""

import subprocess
import os
import time

# Read the actual input
with open('/var/folders/b_/66g1274s7_xfw7x984g072s40000gn/T/gemini_input_0.txt', 'r') as f:
    actual_content = f.read()

print(f"Read actual content: {len(actual_content)} chars")
print(f"First 200 chars: {actual_content[:200]}...")

# Create clean env
clean_env = {}
for key, value in os.environ.items():
    if key != "GOOGLE_APPLICATION_CREDENTIALS":
        clean_env[key] = value

print(f"\nTesting with actual content...")
start = time.time()

try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=actual_content,
        capture_output=True,
        text=True,
        env=clean_env,
        timeout=120
    )
    elapsed = time.time() - start
    print(f"Success in {elapsed:.1f}s!")
    print(f"Output length: {len(result.stdout)}")
    print(f"First 200 chars of output: {result.stdout[:200]}...")
except subprocess.TimeoutExpired:
    elapsed = time.time() - start
    print(f"TIMEOUT after {elapsed:.1f}s")
    print("So it's something specific about this content!")
    
    # Check for special characters
    print("\nChecking for special characters...")
    import re
    nulls = actual_content.count('\x00')
    print(f"Null bytes: {nulls}")
    
    # Check for very long lines
    lines = actual_content.split('\n')
    max_line = max(len(line) for line in lines)
    print(f"Number of lines: {len(lines)}")
    print(f"Max line length: {max_line}")
    
except Exception as e:
    print(f"Error: {e}")