#!/usr/bin/env python3
"""Test with actual input from the script"""

import subprocess
import os
import time

# Read the actual input
with open('/var/folders/b_/66g1274s7_xfw7x984g072s40000gn/T/gemini_input_0.txt', 'r') as f:
    actual_input = f.read()

print(f"Testing with actual input: {len(actual_input)} characters")

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

print("Running gemini...")
start_time = time.time()

try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=actual_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=60  # 60 second timeout
    )
    
    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f} seconds")
    print(f"Exit code: {result.returncode}")
    print(f"Output length: {len(result.stdout)} characters")
    if result.stderr:
        print(f"\nStderr: {result.stderr[:500]}...")
    if result.stdout:
        print(f"\nFirst 500 chars of output:\n{result.stdout[:500]}...")
        
except subprocess.TimeoutExpired:
    elapsed = time.time() - start_time
    print(f"\nTIMEOUT after {elapsed:.1f} seconds!")
    print("The command is hanging with the actual input")
except Exception as e:
    print(f"\nError: {e}")