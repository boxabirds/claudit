#!/usr/bin/env python3
"""Test the gemini CLI subprocess issue"""

import subprocess
import os

print("Testing gemini CLI...")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'not set')}")

# Test 1: Simple test with shell
cmd = """
echo "[TEST] Environment check"
echo "GOOGLE_APPLICATION_CREDENTIALS before: ${GOOGLE_APPLICATION_CREDENTIALS:-not set}"
unset GOOGLE_APPLICATION_CREDENTIALS
echo "GOOGLE_APPLICATION_CREDENTIALS after: ${GOOGLE_APPLICATION_CREDENTIALS:-not set}"
echo "[TEST] Testing gemini..."
echo "Say hello" | gemini -m gemini-2.5-flash
"""

try:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    print(f"\nExit code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    print(f"Stderr:\n{result.stderr}")
except subprocess.TimeoutExpired:
    print("\n[ERROR] Command timed out after 10 seconds!")
except Exception as e:
    print(f"\n[ERROR] {e}")