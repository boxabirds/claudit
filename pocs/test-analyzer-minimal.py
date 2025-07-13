#!/usr/bin/env python3
"""
Minimal test of the analyzer
"""

import subprocess
import sys

# Run analyzer on smallest project with debug output
cmd = [
    sys.executable,
    "/Users/julian/expts/claudit/claudit-analyzer/analyze_claude_history_v2.py",
    "--project-number", "1",
    "--yes"
]

print("Running analyzer...")
print("Command:", ' '.join(cmd))
print("\nWatch for GOOGLE_APPLICATION_CREDENTIALS status in the output...")
print("="*60)

# Run without capturing to see output in real-time
result = subprocess.run(cmd)