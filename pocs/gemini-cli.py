#!/usr/bin/env python3
"""
POC to test different ways of calling gemini CLI
"""

import subprocess
import tempfile
import os

def test_direct_prompt():
    """Test passing prompt directly as argument"""
    print("=== Test 1: Direct prompt as argument ===")
    try:
        cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "What is 2+2? Reply with just the number."]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout[:500] if result.stdout else 'None'}")
        if result.stderr:
            print(f"Error output:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_stdin_approach():
    """Test passing prompt via stdin"""
    print("=== Test 2: Prompt via stdin with -p - ===")
    try:
        prompt = "What is 3+3? Reply with just the number."
        cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "-"]
        result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=15)
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout[:200]}")
        print(f"Error: {result.stderr[:200] if result.stderr else 'None'}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_stdin_without_google_creds():
    """Test stdin approach without GOOGLE_APPLICATION_CREDENTIALS"""
    print("=== Test 2b: Stdin without GOOGLE_APPLICATION_CREDENTIALS ===")
    try:
        prompt = "What is 3+3? Reply with just the number."
        cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "-"]
        
        # Remove GOOGLE_APPLICATION_CREDENTIALS from environment
        env = os.environ.copy()
        if "GOOGLE_APPLICATION_CREDENTIALS" in env:
            del env["GOOGLE_APPLICATION_CREDENTIALS"]
            print("Removed GOOGLE_APPLICATION_CREDENTIALS from environment")
        
        result = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=15, env=env)
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout[:500] if result.stdout else 'None'}")
        if result.stderr:
            print(f"Error output:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_file_path_old_way():
    """Test the old way that was incorrectly passing file path to -p"""
    print("=== Test 3: File path to -p (old incorrect way) ===")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("What is 4+4? Reply with just the number.")
            temp_file = f.name
        
        cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", temp_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout[:500] if result.stdout else 'None'}")
        if result.stderr:
            print(f"Error output:\n{result.stderr}")
        
        # Clean up
        os.unlink(temp_file)
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_large_prompt_stdin():
    """Test large prompt via stdin"""
    print("=== Test 4: Large prompt via stdin ===")
    try:
        # Create a large prompt
        large_prompt = """Analyze this text and tell me what number appears most frequently:
        """ + "The number 7 appears here. " * 100 + """
        Just reply with the number that appears most frequently, nothing else."""
        
        print(f"Prompt size: {len(large_prompt)} characters")
        
        cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "-"]
        result = subprocess.run(cmd, input=large_prompt, capture_output=True, text=True, timeout=15)
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout[:200]}")
        print(f"Error: {result.stderr[:200] if result.stderr else 'None'}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_multiline_prompt_stdin():
    """Test multiline prompt via stdin"""
    print("=== Test 5: Multiline prompt via stdin ===")
    try:
        multiline_prompt = """Please analyze this conversation:

User: Hello
Assistant: Hi there!
User: What's the weather?
Assistant: I don't have access to real-time weather data.

What was the main topic? Reply in one word."""
        
        cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "-"]
        result = subprocess.run(cmd, input=multiline_prompt, capture_output=True, text=True, timeout=15)
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout[:200]}")
        print(f"Error: {result.stderr[:200] if result.stderr else 'None'}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    print("Testing gemini CLI approaches...\n")
    
    # Test different approaches
    test_direct_prompt()
    test_stdin_approach()
    test_stdin_without_google_creds()
    test_file_path_old_way()
    test_large_prompt_stdin()
    test_multiline_prompt_stdin()
    
    print("\nDone!")