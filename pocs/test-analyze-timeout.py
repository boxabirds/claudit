#!/usr/bin/env python3
"""
Test script to debug gemini CLI timeout issues with the analyzer
"""

import subprocess
import os

def test_analyze_with_debug():
    """Run the analyzer with a small test to see debug output"""
    
    # First, let's test if gemini CLI works at all
    print("1. Testing basic gemini CLI...")
    try:
        # Remove Google creds for test
        env = os.environ.copy()
        if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
            del env['GOOGLE_APPLICATION_CREDENTIALS']
            
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input="What is 1+1? One word.",
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        print(f"✓ Basic test: Exit code {result.returncode}")
        print(f"✓ Response: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️  Stderr: {result.stderr}")
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        return
    
    print("\n2. Testing analyzer with a small project...")
    # Run the analyzer with project number 1 (smallest project)
    cmd = [
        "python", 
        "/Users/julian/expts/claudit/claudit-analyzer/analyze_claude_history_v2.py",
        "--project-number", "1",
        "--yes",
        "--force-gemini-cli"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("This will show detailed debug output...\n")
    
    # Run without capturing output so we see it in real-time
    try:
        result = subprocess.run(cmd, timeout=120)
        print(f"\n✓ Analyzer completed with exit code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print(f"\n✗ Analyzer timed out after 120 seconds")
    except Exception as e:
        print(f"\n✗ Analyzer failed: {e}")

if __name__ == "__main__":
    test_analyze_with_debug()