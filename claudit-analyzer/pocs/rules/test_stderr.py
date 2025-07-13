import sys
import subprocess

# Test command that produces both stdout and stderr
cmd = ["python", "-c", """
import sys
print('This is stdout')
print('Error message', file=sys.stderr)
print('More stdout')
sys.exit(1)
"""]

print("Testing stderr handling...")
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")