#!/usr/bin/env python3
"""Test if long lines cause gemini to hang"""

import subprocess
import os

env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

# Test with increasingly long single lines
for line_length in [100, 1000, 10000, 30000]:
    print(f"\n=== Testing with {line_length} char line ===")
    test_input = "Summarize this: " + "x" * line_length
    
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input=test_input,
            capture_output=True,
            text=True,
            env=env,
            timeout=15
        )
        print(f"Success! Output length: {len(result.stdout)}")
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT with {line_length} char line!")
        break
    except Exception as e:
        print(f"Error: {e}")
        break