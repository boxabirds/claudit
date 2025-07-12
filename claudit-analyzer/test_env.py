#!/usr/bin/env python3
"""Test script to debug subprocess environment issues."""

import os
import subprocess
import json
from pathlib import Path

def test_subprocess_env():
    """Test what environment variables are available in subprocess."""
    
    print("=== Current Process Environment ===")
    print(f"HOME: {os.environ.get('HOME', 'NOT SET')}")
    print(f"USER: {os.environ.get('USER', 'NOT SET')}")
    print(f"PATH: {os.environ.get('PATH', 'NOT SET')}")
    
    # Check if gemini oauth file exists
    oauth_path = Path.home() / ".gemini" / "oauth_credentials.json"
    print(f"\nOAuth file exists at {oauth_path}: {oauth_path.exists()}")
    if oauth_path.exists():
        print(f"OAuth file permissions: {oct(oauth_path.stat().st_mode)[-3:]}")
    
    print("\n=== Subprocess Environment (no env specified) ===")
    # Test subprocess without explicit env
    result = subprocess.run(
        ["python3", "-c", "import os; print(f'HOME={os.environ.get(\"HOME\", \"NOT SET\")}')"],
        capture_output=True,
        text=True
    )
    print(f"Subprocess output: {result.stdout.strip()}")
    
    print("\n=== Subprocess with explicit env ===")
    # Test subprocess with explicit env
    env = os.environ.copy()
    result = subprocess.run(
        ["python3", "-c", "import os; print(f'HOME={os.environ.get(\"HOME\", \"NOT SET\")}')"],
        capture_output=True,
        text=True,
        env=env
    )
    print(f"Subprocess output: {result.stdout.strip()}")
    
    # Test gemini CLI directly
    print("\n=== Testing gemini CLI ===")
    gemini_path = subprocess.run(["which", "gemini"], capture_output=True, text=True)
    if gemini_path.returncode == 0:
        print(f"Gemini CLI found at: {gemini_path.stdout.strip()}")
        
        # Try to run gemini with debug info
        print("\nTrying to run gemini CLI to check environment...")
        result = subprocess.run(
            ["gemini", "--version"],
            capture_output=True,
            text=True
        )
        print(f"Version output: {result.stdout}")
        if result.stderr:
            print(f"Version stderr: {result.stderr}")
    else:
        print("Gemini CLI not found in PATH")

if __name__ == "__main__":
    test_subprocess_env()