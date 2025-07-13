#!/usr/bin/env python3
"""
Find the size threshold where gemini CLI starts timing out
"""

import subprocess
import os
import time

def test_size(size_kb):
    """Test with a specific size of input"""
    # Create test content of specified size
    test_content = "Test data. " * (size_kb * 100)  # Roughly size_kb KB
    actual_size = len(test_content)
    
    cmd = ["gemini", "-m", "gemini-2.5-flash"]
    env = os.environ.copy()
    if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
        del env['GOOGLE_APPLICATION_CREDENTIALS']
    
    print(f"\nTesting {size_kb}KB ({actual_size:,} chars)...", end='', flush=True)
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            input=f"Summarize this in one sentence: {test_content}",
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        elapsed = time.time() - start
        output_len = len(result.stdout)
        print(f" ✓ Success in {elapsed:.1f}s (output: {output_len} chars)")
        return True, elapsed
        
    except subprocess.TimeoutExpired:
        print(f" ✗ TIMEOUT after 30s")
        return False, 30
    except Exception as e:
        print(f" ✗ Error: {e}")
        return False, 0

print("Finding size threshold for gemini CLI timeout...")
print("=" * 50)

# Test various sizes
sizes = [1, 10, 50, 100, 200, 500, 1000]
results = []

for size in sizes:
    success, elapsed = test_size(size)
    results.append((size, success, elapsed))
    
    # If we hit a timeout, try to narrow down the threshold
    if not success and len(results) > 1 and results[-2][1]:
        prev_size = results[-2][0]
        print(f"\nNarrowing down between {prev_size}KB and {size}KB...")
        
        # Binary search for threshold
        low, high = prev_size, size
        while high - low > 10:
            mid = (low + high) // 2
            mid_success, _ = test_size(mid)
            if mid_success:
                low = mid
            else:
                high = mid
        
        print(f"\nThreshold appears to be around {low}-{high}KB")
        break
    
    # Small delay between tests
    if success:
        time.sleep(2)

print("\n" + "=" * 50)
print("Summary:")
for size, success, elapsed in results:
    status = "✓ Success" if success else "✗ Timeout"
    print(f"{size:4d}KB: {status} ({elapsed:.1f}s)")