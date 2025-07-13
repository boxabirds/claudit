#!/usr/bin/env python3
"""
POC to test how piping content to gemini CLI works.
Based on the insight that gemini CLI detects piped input via process.stdin.isTTY
and switches to non-interactive mode automatically.
"""

import subprocess
import sys
import time

def test_basic_piping():
    """Test basic piping without -p flag"""
    print("=== Test 1: Basic piping (echo 'text' | gemini) ===")
    
    test_content = "What is 2 + 2? Give a very short answer."
    
    try:
        # This should work: piped input automatically triggers non-interactive mode
        result = subprocess.run(
            ["gemini"],
            input=test_content,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)} chars")
        print(f"Stdout preview: {result.stdout[:200]}...")
        print(f"Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_piping_with_p_flag():
    """Test piping with -p flag"""
    print("\n=== Test 2: Piping with -p flag (echo 'context' | gemini -p 'question') ===")
    
    context = "The sky is blue."
    question = "What color is the sky mentioned in the input?"
    
    try:
        result = subprocess.run(
            ["gemini", "-p", question],
            input=context,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)} chars")
        print(f"Stdout preview: {result.stdout[:200]}...")
        print(f"Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_large_content():
    """Test with larger content (simulating the 100k+ case)"""
    print("\n=== Test 3: Large content piping ===")
    
    # Generate larger content
    large_content = f"""
Analyze this conversation:

{'This is a test line with some content. ' * 1000}

What are the main themes?
"""
    
    print(f"Content size: {len(large_content)} characters")
    
    try:
        result = subprocess.run(
            ["gemini"],
            input=large_content,
            capture_output=True,
            text=True,
            timeout=60  # Longer timeout for large content
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)} chars")
        print(f"Stdout preview: {result.stdout[:200]}...")
        print(f"Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_model_flag():
    """Test with model flag"""
    print("\n=== Test 4: With model flag (gemini -m gemini-2.5-flash) ===")
    
    test_content = "What is the capital of France? Very short answer."
    
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input=test_content,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)} chars")
        print(f"Stdout preview: {result.stdout[:200]}...")
        print(f"Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Testing gemini CLI piping behavior...\n")
    
    # Check if gemini is available
    try:
        subprocess.run(["gemini", "--version"], capture_output=True, check=True)
        print("✓ gemini CLI is available\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ gemini CLI not found. Please install with: pip install google-generativeai")
        sys.exit(1)
    
    tests = [
        test_basic_piping,
        test_piping_with_p_flag,
        test_large_content,
        test_model_flag
    ]
    
    results = []
    for test in tests:
        success = test()
        results.append(success)
        time.sleep(2)  # Rate limiting
    
    print(f"\n=== Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed! Piping to gemini CLI works correctly.")
    else:
        print("✗ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()