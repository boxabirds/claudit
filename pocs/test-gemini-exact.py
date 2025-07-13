#!/usr/bin/env python3
"""
Test the exact gemini command pattern used by analyzer
"""

import subprocess
import os
import time

# Remove GOOGLE_APPLICATION_CREDENTIALS
env = os.environ.copy() 
if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
    del env['GOOGLE_APPLICATION_CREDENTIALS']
    print("✓ Removed GOOGLE_APPLICATION_CREDENTIALS")

# Test 1: Simple test with subprocess.run (like the fixed code)
print("\n=== Test 1: subprocess.run with small input ===")
cmd = ["gemini", "-m", "gemini-2.5-flash"]
test_input = "What is 2+2? One word answer."

start = time.time()
try:
    result = subprocess.run(
        cmd,
        input=test_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.1f}s")
    print(f"✓ Exit code: {result.returncode}")
    print(f"✓ Output: {result.stdout.strip()}")
    if result.stderr:
        print(f"⚠️  Stderr: {result.stderr}")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Failed after {elapsed:.1f}s: {e}")

# Test 2: Larger input (simulating analyzer chunks)
print("\n=== Test 2: Larger input (1MB) ===")
large_input = """Analyze this Claude conversation history and identify:

1. **Significant Decisions**: Key choices made during the project development
2. **Mistakes**: Errors, incorrect approaches, or issues that needed fixing
3. **Milestones**: Important achievements or completed features
4. **Timeline**: A chronological overview of the project's progression

Format the output as a Markdown document with clear sections for each category. 
Include specific examples and quotes where relevant. Include important dates and times.
Be concise but thorough.

This is chunk 1 of 1. Analyze this portion of the conversation:

""" + ("Sample conversation data. " * 30000)  # ~1MB of text

print(f"Input size: {len(large_input):,} chars ({len(large_input.encode('utf-8')):,} bytes)")

start = time.time()
try:
    result = subprocess.run(
        cmd,
        input=large_input,
        capture_output=True,
        text=True,
        env=env,
        timeout=60
    )
    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.1f}s")
    print(f"✓ Exit code: {result.returncode}")
    print(f"✓ Output length: {len(result.stdout):,} chars")
    print(f"✓ Output preview: {result.stdout[:100]}...")
    if result.stderr:
        print(f"⚠️  Stderr: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    elapsed = time.time() - start
    print(f"✗ TIMEOUT after {elapsed:.1f}s")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Failed after {elapsed:.1f}s: {e}")

# Test 3: Using Popen (like the debug logging version)
print("\n=== Test 3: Popen with real-time monitoring ===")
test_input = "What is 3+3? One word answer."

start = time.time()
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
    process.stdin.write(test_input)
    process.stdin.flush()
    process.stdin.close()
    print("Input sent and stdin closed")
    
    # Wait with periodic checks
    while True:
        try:
            returncode = process.wait(timeout=5)
            elapsed = time.time() - start
            print(f"✓ Process completed in {elapsed:.1f}s with exit code: {returncode}")
            
            # Read output
            stdout, stderr = process.communicate()
            print(f"✓ Output: {stdout.strip()}")
            if stderr:
                print(f"⚠️  Stderr: {stderr}")
            break
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            print(f"Still running after {elapsed:.1f}s...")
            if elapsed > 30:
                print("✗ Killing process after 30s")
                process.kill()
                break

except Exception as e:
    print(f"✗ Failed: {e}")