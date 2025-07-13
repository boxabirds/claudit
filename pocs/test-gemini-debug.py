#!/usr/bin/env python3
"""
Debug version with real-time logging to see what's happening
"""

import subprocess
import sys
import os
import time
import threading

def get_clean_env():
    """Get environment with GOOGLE_APPLICATION_CREDENTIALS removed"""
    env = os.environ.copy()
    if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
        del env['GOOGLE_APPLICATION_CREDENTIALS']
        print("🗑️  Removed GOOGLE_APPLICATION_CREDENTIALS from environment")
    return env

def log_subprocess_output(process, name):
    """Log subprocess output in real-time"""
    def read_stdout():
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(f"[{name} STDOUT] {line.rstrip()}")
            process.stdout.close()
    
    def read_stderr():
        if process.stderr:
            for line in iter(process.stderr.readline, ''):
                print(f"[{name} STDERR] {line.rstrip()}")
            process.stderr.close()
    
    # Start threads to read output
    stdout_thread = threading.Thread(target=read_stdout)
    stderr_thread = threading.Thread(target=read_stderr)
    
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    
    stdout_thread.start()
    stderr_thread.start()
    
    return stdout_thread, stderr_thread

def test_simple_command():
    """Test the simplest possible command with logging"""
    print("=== Test: Simple command with real-time logging ===")
    
    test_content = "What is 2+2? One word answer."
    cmd = ["gemini", "-m", "gemini-2.5-flash"]
    env = get_clean_env()
    
    print(f"🚀 Starting command: {' '.join(cmd)}")
    print(f"📝 Input length: {len(test_content)} chars")
    print(f"📝 Input content: {repr(test_content)}")
    print(f"🌍 Environment cleaned: GOOGLE_APPLICATION_CREDENTIALS removed")
    print("⏱️  Starting process...")
    
    start_time = time.time()
    
    try:
        # Use Popen for real-time output
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        print(f"✅ Process started (PID: {process.pid})")
        
        # Start logging threads
        stdout_thread, stderr_thread = log_subprocess_output(process, "gemini")
        
        # Send input and close stdin
        print("📤 Sending input...")
        process.stdin.write(test_content)
        process.stdin.close()
        print("✅ Input sent, stdin closed")
        
        # Wait with timeout
        timeout = 30
        print(f"⏱️  Waiting up to {timeout} seconds for completion...")
        
        try:
            returncode = process.wait(timeout=timeout)
            elapsed = time.time() - start_time
            print(f"✅ Process completed in {elapsed:.1f}s with exit code: {returncode}")
            
            # Wait for output threads to finish
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            
            return returncode == 0
            
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"❌ Process timed out after {elapsed:.1f}s")
            process.kill()
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f}s: {e}")
        return False

def test_with_captured_output():
    """Test with traditional captured output for comparison"""
    print("\n=== Test: Traditional captured output ===")
    
    test_content = "What is 3+3? One word answer."
    cmd = ["gemini", "-m", "gemini-2.5-flash"]
    env = get_clean_env()
    
    print(f"🚀 Starting command: {' '.join(cmd)}")
    print(f"📝 Input: {repr(test_content)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            input=test_content,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Completed in {elapsed:.1f}s")
        print(f"✅ Exit code: {result.returncode}")
        print(f"✅ Stdout: {repr(result.stdout)}")
        print(f"✅ Stderr: {repr(result.stderr)}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"❌ Timeout after {elapsed:.1f}s")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed:.1f}s: {e}")
        return False

def main():
    print("🔍 Debug testing gemini CLI with detailed logging...\n")
    
    # Check environment
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        print(f"⚠️  GOOGLE_APPLICATION_CREDENTIALS: {os.environ['GOOGLE_APPLICATION_CREDENTIALS'][:50]}...")
    else:
        print("✅ GOOGLE_APPLICATION_CREDENTIALS not set")
    
    # Quick version check
    try:
        print("🔍 Checking gemini version...")
        result = subprocess.run(["gemini", "--version"], capture_output=True, text=True, timeout=5)
        print(f"✅ Version: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Version check failed: {e}")
        return
    
    print("\n" + "="*60)
    
    # Run tests
    test1_success = test_simple_command()
    
    print("\n" + "="*60)
    
    test2_success = test_with_captured_output()
    
    print(f"\n🏁 Results:")
    print(f"   Real-time logging test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Captured output test:   {'✅ PASS' if test2_success else '❌ FAIL'}")

if __name__ == "__main__":
    main()