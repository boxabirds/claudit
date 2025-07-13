#!/usr/bin/env python3
"""Find exactly where gemini hangs"""

import subprocess
import os
import time

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

print("Testing progressively larger inputs...")

# Test with increasing sizes
sizes = [10, 100, 1000, 10000, 100000, 500000, 1000000]

for size in sizes:
    print(f"\n=== Testing with {size} chars ===")
    input_text = "x" * size
    
    start = time.time()
    try:
        # Use timeout to avoid hanging forever
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input=input_text,
            capture_output=True,
            text=True,
            env=env,
            timeout=30  # 30 second timeout
        )
        elapsed = time.time() - start
        print(f"Success! Took {elapsed:.2f}s")
        print(f"Output length: {len(result.stdout)}")
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"TIMEOUT after {elapsed:.2f}s - this is where it hangs!")
        print(f"The issue appears at input size: {size} characters")
        break
    except Exception as e:
        print(f"Error: {e}")
        break

print("\nNow testing if it's the subprocess.run specifically...")

# Test with Popen to see if we can get more info
size = 100000  # Use a size that worked
print(f"\n=== Testing Popen with {size} chars ===")
proc = subprocess.Popen(
    ["gemini", "-m", "gemini-2.5-flash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE,
    text=True,
    env=env
)

input_text = "x" * size
print("Writing to stdin...")
proc.stdin.write(input_text)
print("Flushing stdin...")
proc.stdin.flush()
print("Closing stdin...")
proc.stdin.close()
print("Waiting for process...")

start = time.time()
try:
    stdout, stderr = proc.communicate(timeout=30)
    print(f"Success! Took {time.time() - start:.2f}s")
    print(f"Output: {len(stdout)} chars")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT in communicate after {time.time() - start:.2f}s")
    proc.kill()