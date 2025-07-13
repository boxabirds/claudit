#!/usr/bin/env python3
"""
Test the streamlined analyzer CLI
"""

import subprocess
import os

# First verify gemini CLI works without GOOGLE_APPLICATION_CREDENTIALS
print("1. Testing gemini CLI directly...")
env = os.environ.copy()
if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
    del env['GOOGLE_APPLICATION_CREDENTIALS']
    
result = subprocess.run(
    ["gemini", "-m", "gemini-2.5-flash"],
    input="What is 7+7? One word.",
    capture_output=True,
    text=True,
    timeout=10,
    env=env
)
print(f"✓ Gemini test: {result.stdout.strip()}")

print("\n2. Testing analyzer with streamlined CLI...")
# Run with smallest project
cmd = [
    "python",
    "/Users/julian/expts/claudit/claudit-analyzer/analyze_claude_history_v2.py", 
    "--project-number", "1",
    "--yes",
    "--output", "test_streamlined.md"
]

print(f"Running: {' '.join(cmd)}")
print("This should:")
print("- Auto-detect and use Gemini CLI")
print("- Ignore GOOGLE_APPLICATION_CREDENTIALS automatically")
print("- Not prompt for any user input")
print("\n" + "="*60)

# Run and show output
subprocess.run(cmd)