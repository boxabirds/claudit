#!/usr/bin/env python3
"""Minimal test to replicate the exact hanging issue"""

import subprocess
import os

# Read the actual input that's causing issues
with open('/var/folders/b_/66g1274s7_xfw7x984g072s40000gn/T/gemini_input_0.txt', 'r') as f:
    actual_input = f.read()

print(f"Input size: {len(actual_input)} characters")
print("First 200 chars:", actual_input[:200])

# Method 1: Clean environment (what the script does now)
print("\n=== Testing with clean environment (subprocess.run) ===")
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("Removed GOOGLE_APPLICATION_CREDENTIALS")

cmd = ["gemini", "-m", "gemini-2.5-flash"]
print(f"Running: {' '.join(cmd)}")

try:
    # This is EXACTLY what the script does
    result = subprocess.run(
        cmd,
        input=actual_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    print(f"Success! Exit code: {result.returncode}")
    print(f"Output length: {len(result.stdout)}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
except subprocess.TimeoutExpired:
    print("TIMEOUT after 30 seconds!")
    print("This confirms the hanging issue")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Shell with explicit unset (original approach)  
print("\n=== Testing with shell unset ===")
shell_cmd = """
unset GOOGLE_APPLICATION_CREDENTIALS
gemini -m gemini-2.5-flash
"""

try:
    result = subprocess.run(
        shell_cmd,
        input=actual_input,
        capture_output=True,
        text=True,
        shell=True,
        timeout=30
    )
    print(f"Success! Exit code: {result.returncode}")
    print(f"Output length: {len(result.stdout)}")
except subprocess.TimeoutExpired:
    print("TIMEOUT after 30 seconds!")
except Exception as e:
    print(f"Error: {e}")