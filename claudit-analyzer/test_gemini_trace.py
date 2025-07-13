#!/usr/bin/env python3
"""Trace exactly what's happening with gemini"""

import subprocess
import os
import time
import sys

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("Removed GOOGLE_APPLICATION_CREDENTIALS from env")

# Test 1: Simple echo test
print("\n=== Test 1: Simple echo ===")
start = time.time()
result = subprocess.run(
    ["echo", "test"],
    capture_output=True,
    text=True,
    env=env
)
print(f"Echo completed in {time.time() - start:.2f}s")

# Test 2: Gemini with tiny input
print("\n=== Test 2: Gemini with tiny input ===")
start = time.time()
proc = subprocess.Popen(
    ["gemini", "-m", "gemini-2.5-flash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)
print("Process started, sending input...")
stdout, stderr = proc.communicate(input="Say hello", timeout=10)
print(f"Completed in {time.time() - start:.2f}s")
print(f"Output: {stdout[:50]}")

# Test 3: Check if stdin is the issue
print("\n=== Test 3: Large input test ===")
large_input = "Analyze this: " + "x" * 1000000  # 1MB
start = time.time()
proc = subprocess.Popen(
    ["gemini", "-m", "gemini-2.5-flash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)
print("Process started, sending 1MB input...")
try:
    stdout, stderr = proc.communicate(input=large_input, timeout=60)
    print(f"Completed in {time.time() - start:.2f}s")
    print(f"Output length: {len(stdout)}")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT after {time.time() - start:.2f}s")
    proc.kill()
    
# Test 4: Check process state
print("\n=== Test 4: Process monitoring ===")
proc = subprocess.Popen(
    ["gemini", "-m", "gemini-2.5-flash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)
print(f"Process PID: {proc.pid}")
print("Sending input...")
proc.stdin.write("Say hello\n")
proc.stdin.flush()
proc.stdin.close()
print("Input sent and stdin closed")

# Poll for 5 seconds
for i in range(10):
    time.sleep(0.5)
    poll = proc.poll()
    if poll is not None:
        print(f"Process finished with code {poll} after {(i+1)*0.5}s")
        stdout = proc.stdout.read()
        print(f"Output: {stdout[:50]}")
        break
    else:
        print(f"Still running after {(i+1)*0.5}s...")
        
if proc.poll() is None:
    print("Process still running, killing it")
    proc.kill()

# Test 5: Exact replication of script's approach
print("\n=== Test 5: Exact script replication ===")
input_text = "Analyze this: " + "x" * 1000000  # 1MB like the script
start = time.time()
result = subprocess.run(
    ["gemini", "-m", "gemini-2.5-flash"],
    input=input_text,
    capture_output=True,
    text=True,
    env=env,
    timeout=60
)
print(f"Completed in {time.time() - start:.2f}s")
print(f"Exit code: {result.returncode}")
print(f"Output length: {len(result.stdout)}")
if result.stderr:
    print(f"Stderr: {result.stderr[:200]}")

# Test 6: Test with actual JSON content structure
print("\n=== Test 6: JSON-like content ===")
json_content = """Analyze this Claude conversation history:
{"message": {"role": "user", "content": "test"}, "timestamp": "2025-06-22T05:34:49.930Z"}
""" * 1000  # Repeat to make it bigger
start = time.time()
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=json_content,
        capture_output=True,
        text=True,
        env=env,
        timeout=60
    )
    print(f"Completed in {time.time() - start:.2f}s")
    print(f"Output length: {len(result.stdout)}")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT after {time.time() - start:.2f}s")