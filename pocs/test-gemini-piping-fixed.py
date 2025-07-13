#!/usr/bin/env python3
"""
POC to test piping content to gemini CLI with proper environment handling.
Key insights:
1. Use -m gemini-2.5-flash to avoid Pro quota limits
2. Remove GOOGLE_APPLICATION_CREDENTIALS from environment 
3. Piped input automatically triggers non-interactive mode
"""

import subprocess
import sys
import os
import time

def get_clean_env():
    """Get environment with GOOGLE_APPLICATION_CREDENTIALS removed"""
    env = os.environ.copy()
    if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
        del env['GOOGLE_APPLICATION_CREDENTIALS']
        print("🗑️  Removed GOOGLE_APPLICATION_CREDENTIALS from environment")
    return env

def test_basic_piping():
    """Test basic piping with flash model"""
    print("=== Test 1: Basic piping with flash model ===")
    
    test_content = "What is 2 + 2? Give a very short answer."
    
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input=test_content,
            capture_output=True,
            text=True,
            timeout=30,
            env=get_clean_env()
        )
        
        print(f"✓ Exit code: {result.returncode}")
        print(f"✓ Stdout length: {len(result.stdout)} chars")
        print(f"✓ Response: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️  Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_large_content():
    """Test with larger content (simulating chunked analysis)"""
    print("\n=== Test 2: Large content piping ===")
    
    # Generate larger content (similar to conversation chunks)
    large_content = f"""
Analyze this conversation data:

User: I need help with my Python code
Assistant: I'd be happy to help! What specific issue are you having?
User: My loop isn't working correctly
Assistant: Could you share the code so I can take a look?

{'This pattern repeats many times in the conversation. ' * 200}

What are the main themes in this conversation?
"""
    
    print(f"📏 Content size: {len(large_content):,} characters")
    
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash"],
            input=large_content,
            capture_output=True,
            text=True,
            timeout=60,
            env=get_clean_env()
        )
        
        print(f"✓ Exit code: {result.returncode}")
        print(f"✓ Stdout length: {len(result.stdout):,} chars")
        print(f"✓ Response preview: {result.stdout[:200]}...")
        if result.stderr:
            print(f"⚠️  Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_with_prompt_flag():
    """Test with -p flag (like consolidation)"""
    print("\n=== Test 3: With -p flag for consolidation ===")
    
    context = "Here are some analysis results to consolidate..."
    prompt = "Summarize the key points from the input data:"
    
    try:
        result = subprocess.run(
            ["gemini", "-m", "gemini-2.5-flash", "-p", prompt],
            input=context,
            capture_output=True,
            text=True,
            timeout=30,
            env=get_clean_env()
        )
        
        print(f"✓ Exit code: {result.returncode}")
        print(f"✓ Stdout length: {len(result.stdout)} chars")
        print(f"✓ Response: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️  Stderr: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("🧪 Testing gemini CLI piping behavior with proper environment...\n")
    
    # Check environment
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        print(f"⚠️  GOOGLE_APPLICATION_CREDENTIALS is set to: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
        print("Will remove it for subprocess calls\n")
    else:
        print("✓ GOOGLE_APPLICATION_CREDENTIALS not set\n")
    
    # Check if gemini is available
    try:
        result = subprocess.run(["gemini", "--version"], capture_output=True, check=True, env=get_clean_env())
        print(f"✓ gemini CLI is available: {result.stdout.decode().strip()}\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ gemini CLI not found. Please install with: pip install google-generativeai")
        sys.exit(1)
    
    tests = [
        test_basic_piping,
        test_large_content,
        test_with_prompt_flag,
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        success = test()
        results.append(success)
        if i < len(tests):  # Don't sleep after last test
            print("⏱️  Rate limiting pause...")
            time.sleep(3)
    
    print(f"\n🏁 Summary")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All tests passed! Piping to gemini CLI works correctly.")
        print("\n💡 Key findings:")
        print("   - Use 'gemini -m gemini-2.5-flash' to avoid Pro quota limits")
        print("   - Remove GOOGLE_APPLICATION_CREDENTIALS from subprocess environment")
        print("   - Piped input automatically triggers non-interactive mode")
        print("   - Large content works fine via stdin")
    else:
        print("❌ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()