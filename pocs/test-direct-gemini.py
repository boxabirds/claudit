#!/usr/bin/env python3
"""
Test gemini CLI directly with the exact conditions
"""

import subprocess
import os
import sys

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("✓ Removed GOOGLE_APPLICATION_CREDENTIALS")

# Test with a large input like the analyzer
test_input = "You are an expert. " * 50000  # ~1MB
print(f"Input size: {len(test_input)} chars")

cmd = ["gemini", "-m", "gemini-2.5-flash"]
print(f"Running: {' '.join(cmd)}")

# Try with Popen like the analyzer does
print("\nUsing Popen (like analyzer)...")
try:
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    print(f"Process started with PID: {process.pid}")
    
    # Send input
    print("Sending input...")
    stdout, stderr = process.communicate(input=test_input, timeout=30)
    
    print(f"Exit code: {process.returncode}")
    print(f"Output length: {len(stdout)} chars")
    print(f"Output preview: {stdout[:100]}...")
    if stderr:
        print(f"Stderr: {stderr[:200]}")
        
except subprocess.TimeoutExpired:
    print("✗ TIMEOUT!")
    process.kill()
    # Try to get any output
    try:
        stdout, stderr = process.communicate(timeout=1)
        if stdout:
            print(f"Partial stdout: {stdout[:200]}")
        if stderr:
            print(f"Partial stderr: {stderr[:200]}")
    except:
        pass
except Exception as e:
    print(f"✗ Error: {e}")