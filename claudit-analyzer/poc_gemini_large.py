#!/usr/bin/env python3
"""POC to test gemini with large input like the actual script"""

import subprocess
import os
import tempfile

# Create a large test content similar to what causes the issue
print("Creating large test content...")
large_content = """You are an AI assistant analyzing conversation history.

## Task: Knowledge Extraction

Extract key knowledge from this conversation:

""" + ("This is a test line of conversation content. " * 100 + "\n") * 10000  # ~1MB of content

print(f"Content size: {len(large_content)} characters")

# Save to file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write(large_content)
    input_file = f.name

print(f"Saved to: {input_file}")

# Test with shell command exactly like the script
shell_cmd = f"""
echo "[DEBUG] GOOGLE_APPLICATION_CREDENTIALS before: ${{GOOGLE_APPLICATION_CREDENTIALS:-not set}}" >&2
unset GOOGLE_APPLICATION_CREDENTIALS
echo "[DEBUG] GOOGLE_APPLICATION_CREDENTIALS after: ${{GOOGLE_APPLICATION_CREDENTIALS:-not set}}" >&2
echo "[DEBUG] Running: gemini -m gemini-2.5-flash" >&2
cat {input_file} | gemini -m gemini-2.5-flash
"""

print("\nRunning gemini with large input...")
print("Shell command:")
print(shell_cmd)

try:
    process = subprocess.Popen(
        shell_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True
    )
    
    print("\nWaiting for process (30s timeout)...")
    stdout, stderr = process.communicate(timeout=30)
    
    print(f"\nSuccess! Exit code: {process.returncode}")
    print(f"Output length: {len(stdout)} characters")
    print(f"First 200 chars of output: {stdout[:200]}...")
    print(f"\nStderr:")
    print(stderr)
    
except subprocess.TimeoutExpired:
    print("\nTIMEOUT after 30 seconds!")
    print("Process is hanging. Killing it...")
    process.kill()
    stdout, stderr = process.communicate()
    print(f"\nPartial stdout: {stdout[:200] if stdout else 'None'}")
    print(f"Stderr: {stderr}")
    print(f"\nTest the command manually:")
    print(f"cat {input_file} | gemini -m gemini-2.5-flash")
    
print(f"\nInput file kept at: {input_file}")