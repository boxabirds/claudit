#!/usr/bin/env python3
"""Debug environment variable issue"""

import subprocess
import os

print(f"Parent process GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# Method 1: Using env dict
env1 = os.environ.copy()
if "GOOGLE_APPLICATION_CREDENTIALS" in env1:
    del env1["GOOGLE_APPLICATION_CREDENTIALS"]

# Method 2: Set to empty
env2 = os.environ.copy()
env2["GOOGLE_APPLICATION_CREDENTIALS"] = ""

# Method 3: Use None env
env3 = None

# Test what the subprocess sees
test_script = """
import os
print(f"Subprocess sees GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
"""

print("\nMethod 1: Delete from env dict")
result = subprocess.run(["python", "-c", test_script], env=env1, capture_output=True, text=True)
print(result.stdout)

print("Method 2: Set to empty string")
result = subprocess.run(["python", "-c", test_script], env=env2, capture_output=True, text=True)
print(result.stdout)

print("Method 3: env=None (inherits parent)")
result = subprocess.run(["python", "-c", test_script], env=env3, capture_output=True, text=True)
print(result.stdout)

# Now test gemini with a tiny input
print("\nTesting gemini with 'hi' input...")
for i, env in enumerate([env1, env2, env3]):
    print(f"\nMethod {i+1}:")
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input="hi",
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )
        print(f"Success! Output: {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")