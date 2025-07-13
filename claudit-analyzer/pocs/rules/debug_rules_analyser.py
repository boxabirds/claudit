PROMPT = """
You are an expert corporate performance psychologist. 
You have deep insight into the human psyche. 
Your job is to analyse the provided conversations between the AI assistant 
and the User to produce a list of up to 100 incidents in the conversation 
where the assistant upset, angered, frustrated, or confused the user due to not meeting expectations, 
being unprofessional, lazy, ambiguous, whimsical, lacking tenacity, incompetent, or stupid. 
The goal is collating a list of corrective and preventative rules for the assistant to avoid having them happen again. 

Format each incident as:
- What happened: [specific behavior]
- Rule: [corrective action]
- Example: [quote from conversation if applicable]

Here is the conversation to analyse:
"""

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
from typing import Optional
import sys

def read_jsonl_file(file_path: Path) -> str:
    content = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    # Filter to keep only essential fields
                    filtered_data = {}
                    
                    # Always keep these fields if they exist
                    if 'message' in data:
                        filtered_data['message'] = data['message']
                    if 'timestamp' in data:
                        filtered_data['timestamp'] = data['timestamp']
                    if 'children' in data:
                        filtered_data['children'] = data['children']
                    
                    # Keep type to understand the structure
                    if 'type' in data:
                        filtered_data['type'] = data['type']
                    
                    # Strip images from toolUseResult if present
                    if 'toolUseResult' in data:
                        filtered_data['toolUseResult'] = data['toolUseResult']
                    
                    # Only add if we have meaningful content
                    if filtered_data and ('message' in filtered_data or 'type' in filtered_data):
                        content.append(json.dumps(filtered_data))
                except json.JSONDecodeError:
                    pass  # Silently skip invalid lines
    
    return "\n".join(content)


def run_debug(cmd, input_text):
    clean_env = {}
    for key, value in os.environ.items():
        if key != "GOOGLE_APPLICATION_CREDENTIALS":
            clean_env[key] = value
    
    print(f"Environment has {len(clean_env)} vars (removed GOOGLE_APPLICATION_CREDENTIALS)", flush=True)
    print(f"Command: {' '.join(cmd)}", flush=True)
    print(f"Input text length: {len(input_text)} chars", flush=True)
    print(f"First 200 chars of input: {input_text[:200]}...", flush=True)
    
    # Run without capturing output so we can see what's happening
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr to stdout
        text=True,
        env=clean_env,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Write input and close stdin
    print("\n--- Writing input to subprocess stdin ---", flush=True)
    proc.stdin.write(input_text)
    proc.stdin.close()
    
    print("\n--- Subprocess output (real-time) ---", flush=True)
    
    # Read output line by line
    output_lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print(f"[subprocess]: {line}", end='', flush=True)
        output_lines.append(line)
    
    # Wait for process to complete
    return_code = proc.wait()
    
    print(f"\n--- Process completed with exit code: {return_code} ---", flush=True)
    
    return return_code, ''.join(output_lines)


# Test with a smaller prompt first
print("=== Testing with simple prompt first ===", flush=True)
simple_cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", "Say hello"]
try:
    code, output = run_debug(simple_cmd, "")
    print(f"Simple test result: {code}", flush=True)
except Exception as e:
    print(f"Simple test error: {e}", flush=True)

print("\n=== Now testing with full prompt ===", flush=True)
cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", PROMPT]
text = read_jsonl_file(Path("small.jsonl"))
code, output = run_debug(cmd, text)

if code != 0:
    print(f"\nError: Command failed with exit code {code}", flush=True)
    sys.exit(1)