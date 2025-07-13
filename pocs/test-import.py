#!/usr/bin/env python3
"""
Test if we can even import the analyzer
"""

print("Starting import test...")

try:
    print("1. Importing sys...")
    import sys
    print("✓ sys imported")
    
    print("2. Adding path...")
    sys.path.insert(0, '/Users/julian/expts/claudit/claudit-analyzer')
    print("✓ Path added")
    
    print("3. Importing analyzer module...")
    import analyze_claude_history_v2
    print("✓ Module imported")
    
    print("4. Checking if gemini is available...")
    import shutil
    if shutil.which("gemini"):
        print("✓ gemini CLI found")
    else:
        print("✗ gemini CLI not found")
    
    print("\nImport successful!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()