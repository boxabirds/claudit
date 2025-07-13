#!/usr/bin/env python3
"""
Create a simplified version of run_gemini_cli_with_logging
"""

import subprocess
import os
import time

def run_gemini_cli_simple(cmd, input_text, attempt=0):
    """Simplified version without complex threading"""
    print(f"\n═══ Gemini CLI Call (Attempt {attempt + 1}) ═══", flush=True)
    print(f"Command: {' '.join(cmd)}", flush=True)
    print(f"Input length: {len(input_text)} chars", flush=True)
    
    env = os.environ.copy()
    if "GOOGLE_APPLICATION_CREDENTIALS" in env:
        del env["GOOGLE_APPLICATION_CREDENTIALS"]
        print("Removed GOOGLE_APPLICATION_CREDENTIALS", flush=True)
    
    print(f"Starting process at {time.strftime('%H:%M:%S')}...", flush=True)
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        print(f"Process started with PID: {process.pid}", flush=True)
        print("Calling communicate()...", flush=True)
        
        # Simple communicate with timeout
        stdout, stderr = process.communicate(input=input_text, timeout=30)
        
        print(f"Process completed with exit code: {process.returncode}", flush=True)
        print(f"Output length: {len(stdout)} chars", flush=True)
        
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after 30 seconds!", flush=True)
        process.kill()
        stdout, stderr = process.communicate()
        raise
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

# Test with actual analyzer prompt
prompt = """You are an expert corporate performance psychologist..."""  # shortened for test
test_input = prompt + "\n\nAnalyze this:\n\n" + ("test data " * 10000)

cmd = ["gemini", "-m", "gemini-2.5-flash"]
print(f"Testing with {len(test_input)} chars of input...")

try:
    result = run_gemini_cli_simple(cmd, test_input)
    print(f"\nSuccess! Output preview: {result.stdout[:100]}...")
except Exception as e:
    print(f"\nFailed: {e}")