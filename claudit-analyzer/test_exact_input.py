#!/usr/bin/env python3
"""Test with exact input from the script"""

import subprocess
import os

# Read the exact input file
input_file = '/var/folders/b_/66g1274s7_xfw7x984g072s40000gn/T/gemini_input_0.txt'
if os.path.exists(input_file):
    with open(input_file, 'r') as f:
        actual_input = f.read()
    print(f"Read input file: {len(actual_input)} characters")
else:
    print("Input file doesn't exist, using test data")
    actual_input = "Analyze this: " + "x" * 100000

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

# Test 1: First 1000 chars
print("\n=== Test 1: First 1000 chars ===")
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=actual_input[:1000],
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    print(f"Success! Output: {len(result.stdout)} chars")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")

# Test 2: Shell command (like the script was trying)
print("\n=== Test 2: Via shell ===")
with open('/tmp/test_input.txt', 'w') as f:
    f.write(actual_input[:1000])

cmd = 'unset GOOGLE_APPLICATION_CREDENTIALS && cat /tmp/test_input.txt | gemini -m gemini-2.5-flash'
try:
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30
    )
    print(f"Success via shell! Output: {len(result.stdout)} chars")
except subprocess.TimeoutExpired:
    print("TIMEOUT via shell!")

# Test 3: Check the actual script's run method
print("\n=== Test 3: Replicate script's exact method ===")
cmd = ["gemini", "-m", "gemini-2.5-flash"]
print(f"Running: {' '.join(cmd)}")
print(f"With env that has GOOGLE_APPLICATION_CREDENTIALS removed: {'GOOGLE_APPLICATION_CREDENTIALS' not in env}")

try:
    result = subprocess.run(
        cmd,
        input=actual_input[:10000],  # Try 10K first
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    print(f"10K chars success! Output: {len(result.stdout)} chars")
    
    # Now try full size
    print("\n=== Test 4: Full input ===")
    result = subprocess.run(
        cmd,
        input=actual_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=60
    )
    print(f"Full input success! Output: {len(result.stdout)} chars")
    
except subprocess.TimeoutExpired as e:
    print(f"TIMEOUT! This is the issue")
    print(f"The command hangs with this specific input")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")