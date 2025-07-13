#!/usr/bin/env python3
"""POC to test gemini subprocess hanging issue"""

import subprocess
import os
import tempfile
import time

# Test content similar to what the script sends
test_content = """You are an AI assistant analyzing conversation history.

Extract knowledge from this conversation:

[User]: How do I implement a CLI tool?
[Assistant]: To implement a CLI tool, you'll need to...

Please analyze and provide insights."""

print("POC: Testing gemini subprocess calls")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'not set')}")

# Method 1: Simple subprocess.run with env manipulation
print("\n=== Method 1: Simple subprocess.run with clean env ===")
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]
    print("Removed GOOGLE_APPLICATION_CREDENTIALS from env")

try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash"],
        input=test_content,
        capture_output=True,
        text=True,
        timeout=10,
        env=env
    )
    print(f"Success! Exit code: {result.returncode}")
    print(f"Output length: {len(result.stdout)}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Shell command with unset
print("\n=== Method 2: Shell with unset ===")
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(test_content)
    input_file = f.name

shell_cmd = f"""
echo "[DEBUG] GOOGLE_APPLICATION_CREDENTIALS before: ${{GOOGLE_APPLICATION_CREDENTIALS:-not set}}" >&2
unset GOOGLE_APPLICATION_CREDENTIALS
echo "[DEBUG] GOOGLE_APPLICATION_CREDENTIALS after: ${{GOOGLE_APPLICATION_CREDENTIALS:-not set}}" >&2
cat {input_file} | gemini -m gemini-2.5-flash
"""

try:
    result = subprocess.run(
        shell_cmd,
        capture_output=True,
        text=True,
        shell=True,
        timeout=10
    )
    print(f"Success! Exit code: {result.returncode}")
    print(f"Output length: {len(result.stdout)}")
    print(f"Stderr: {result.stderr}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
    print(f"Input file: {input_file}")
except Exception as e:
    print(f"Error: {e}")

# Method 3: With Popen (like the script)
print("\n=== Method 3: Popen with real-time output ===")
process = subprocess.Popen(
    shell_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True
)

print("Waiting for process...")
try:
    stdout, stderr = process.communicate(timeout=10)
    print(f"Success! Exit code: {process.returncode}")
    print(f"Output length: {len(stdout)}")
    print(f"Stderr: {stderr}")
except subprocess.TimeoutExpired:
    print("TIMEOUT! Killing process...")
    process.kill()
    stdout, stderr = process.communicate()
    print(f"Partial stdout: {stdout[:100]}")
    print(f"Partial stderr: {stderr}")

# Cleanup
try:
    os.unlink(input_file)
except:
    pass