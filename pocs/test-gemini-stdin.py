#!/usr/bin/env python3
"""Test different ways to pass stdin to gemini CLI"""

import subprocess
import os

# Remove Google credentials for testing
env = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env:
    del env["GOOGLE_APPLICATION_CREDENTIALS"]

prompt = "What is 2+2? Reply with just the number."

print("=== Test 1: Using -p with dash ===")
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash", "-p", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=10,
        env=env
    )
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr[:200] if result.stderr else 'None'}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
print()

print("=== Test 2: Using -p with the prompt directly ===")
try:
    result = subprocess.run(
        ["gemini", "-m", "gemini-2.5-flash", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=10,
        env=env
    )
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr[:200] if result.stderr else 'None'}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
print()

print("=== Test 3: Using echo and pipe ===")
try:
    result = subprocess.run(
        f'echo "{prompt}" | gemini -m gemini-2.5-flash -p -',
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
        env=env
    )
    print(f"Exit code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr[:200] if result.stderr else 'None'}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
print()

print("=== Test 4: Using Popen with communicate ===")
try:
    proc = subprocess.Popen(
        ["gemini", "-m", "gemini-2.5-flash", "-p", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    stdout, stderr = proc.communicate(input=prompt, timeout=10)
    print(f"Exit code: {proc.returncode}")
    print(f"Stdout: {stdout}")
    print(f"Stderr: {stderr[:200] if stderr else 'None'}")
except subprocess.TimeoutExpired:
    print("TIMEOUT!")
    proc.kill()
print()

print("=== Test 5: Check if -p flag expects stdin at all ===")
try:
    # Maybe -p doesn't support stdin?
    result = subprocess.run(
        ["gemini", "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )
    # Look for -p flag documentation
    for line in result.stdout.split('\n'):
        if '-p' in line or '--prompt' in line:
            print(f"Help for -p: {line.strip()}")
except Exception as e:
    print(f"Error: {e}")