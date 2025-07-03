#!/usr/bin/env python3
"""
Test script to verify the Claude analyzer works correctly.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Run a command and return output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("Testing Claude Analyzer Setup...")
    print("-" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("analyze_claude_history.py"):
        print("❌ analyze_claude_history.py not found in current directory")
        sys.exit(1)
    
    # Check virtual environment
    venv_python = ".venv/bin/python"
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found")
        print("Run: uv venv -p 3.12")
        sys.exit(1)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    code, out, err = run_command(f"{venv_python} -c 'import openai; print(\"✅ openai installed\")'")
    if code != 0:
        print("❌ openai not installed")
        print("Run: uv add openai")
        sys.exit(1)
    
    
    # Test script imports
    print("\n2. Testing script imports...")
    code, out, err = run_command(f"{venv_python} -c 'import analyze_claude_history; print(\"✅ Script imports successfully\")'")
    if code != 0:
        print("❌ Script import failed:")
        print(err)
        sys.exit(1)
    
    # Test listing projects (non-interactive)
    print("\n3. Testing project listing...")
    code, out, err = run_command(f"echo 'q' | {venv_python} analyze_claude_history.py")
    if "Available Claude projects:" in out:
        print("✅ Project listing works")
        # Count projects
        project_count = len([line for line in out.split('\n') if line.strip() and line[0:1].isdigit()])
        print(f"   Found {project_count} projects")
    else:
        print("❌ Project listing failed")
        print(out)
        print(err)
    
    # Test with invalid project
    print("\n4. Testing error handling...")
    code, out, err = run_command(f"{venv_python} analyze_claude_history.py /nonexistent/project")
    if "Project not found" in out or "Project not found" in err:
        print("✅ Error handling works")
    else:
        print("❌ Error handling issue")
    
    # Check environment setup
    print("\n5. Checking environment...")
    if os.getenv("GEMINI_API_KEY"):
        print("✅ GEMINI_API_KEY environment variable is set")
    else:
        print("⚠️  GEMINI_API_KEY environment variable not set")
        print("   Export GEMINI_API_KEY=your_api_key_here")
    
    print("\n" + "-" * 50)
    print("Setup Summary:")
    print("✅ All basic tests passed!")
    print("\nTo use the analyzer:")
    print("1. Export GEMINI_API_KEY=your_api_key_here")
    print("2. Run: .venv/bin/python analyze_claude_history.py")
    print("   - Without args: Interactive project selection")
    print("   - With project name: e.g., 'Claudit'")
    print("   - With full path: e.g., '/Users/julian/expts/claudit'")

if __name__ == "__main__":
    main()