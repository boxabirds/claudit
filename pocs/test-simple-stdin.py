#!/usr/bin/env python3
"""Simple test to see what gemini expects"""

import subprocess
import sys

print("Testing what happens when we run: gemini -m gemini-2.5-flash -p -")
print("This should read from stdin if '-p -' syntax is supported")
print()

# Test with a very simple prompt
cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "-"]
prompt = "Say hello"

print(f"Command: {' '.join(cmd)}")
print(f"Input to stdin: '{prompt}'")
print("Running with 5 second timeout...")
print()

try:
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send input and close stdin
    stdout, stderr = proc.communicate(input=prompt + "\n", timeout=5)
    
    print(f"Exit code: {proc.returncode}")
    print(f"Stdout length: {len(stdout)} chars")
    if stdout:
        print(f"Stdout preview: {stdout[:200]}...")
    print(f"Stderr length: {len(stderr)} chars")
    if stderr:
        print(f"Stderr preview: {stderr[:500]}...")
        
except subprocess.TimeoutExpired:
    print("TIMEOUT - process is hanging!")
    print("This suggests gemini is waiting for something...")
    proc.kill()
    stdout, stderr = proc.communicate()
    if stderr:
        print(f"Stderr after kill: {stderr}")
except Exception as e:
    print(f"Error: {e}")