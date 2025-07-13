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
import time
import tiktoken

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


def estimate_tokens(text, model="cl100k_base"):
    """Estimate token count using tiktoken"""
    try:
        enc = tiktoken.get_encoding(model)
        return len(enc.encode(text))
    except Exception as e:
        print(f"Warning: Could not estimate tokens: {e}")
        return None

def run(cmd, input_text):
    clean_env = os.environ.copy()
    clean_env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    
    print(f"Environment has {len(clean_env)} vars (removed GOOGLE_APPLICATION_CREDENTIALS)", flush=True)
    print(f"Running command: {' '.join(cmd)}", flush=True)
    print(f"Input size: {len(input_text)} chars", flush=True)
    
    # Estimate tokens
    token_count = estimate_tokens(input_text)
    if token_count:
        print(f"Estimated input tokens: {token_count:,}", flush=True)
    
    print(f"Processing... (this may take a minute for large inputs)\n", flush=True)
    
    start_time = time.time()
    
    # Use Popen for real-time output
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=clean_env,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Write input and close stdin
    print("--- Writing input to subprocess stdin ---", flush=True)
    proc.stdin.write(input_text)
    proc.stdin.close()
    
    print("\n--- Subprocess output (real-time) ---", flush=True)
    
    # Simple approach: merge stderr to stdout for real-time display
    # For more complex needs, we'd use threading
    output_lines = []
    error_lines = []
    
    # Read from both streams using threads to avoid blocking
    import threading
    
    def read_stream(stream, lines, prefix):
        for line in stream:
            print(f"[{prefix}]: {line}", end='', flush=True)
            lines.append(line)
    
    # Start threads for reading
    stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, output_lines, "stdout"))
    stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, error_lines, "stderr"))
    
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait for process to complete
    return_code = proc.wait()
    
    # Wait for threads to finish reading
    stdout_thread.join()
    stderr_thread.join()
    
    elapsed_time = time.time() - start_time
    
    print(f"\n--- Process completed with exit code: {return_code} ---", flush=True)
    print(f"Output length: {len(''.join(output_lines))} chars", flush=True)
    print(f"Processing time: {elapsed_time:.2f} seconds", flush=True)
    
    # Create a result-like object
    class Result:
        def __init__(self, returncode, stdout, stderr):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
    
    result = Result(return_code, ''.join(output_lines), ''.join(error_lines))
    
    if return_code != 0:
        print(f"\nError output captured: {len(result.stderr)} chars")
        raise subprocess.CalledProcessError(return_code, cmd, result.stdout, result.stderr)
        
    return result, elapsed_time


def main(input_file="small.jsonl"):
    input_path = Path(input_file)
    output_file = input_path.stem + "-rules.md"
    
    print(f"Reading from: {input_file}")
    print(f"Will write to: {output_file}")
    
    cmd = ["gemini", "-m", "gemini-2.5-flash", "-p", PROMPT]
    text = read_jsonl_file(input_path)
    
    # Combine prompt and text for token estimation
    full_input = PROMPT + "\n" + text
    total_tokens = estimate_tokens(full_input)
    
    result, elapsed_time = run(cmd, text)
    
    # Write results to markdown file
    with open(output_file, 'w') as f:
        f.write(f"# Analysis Results for {input_file}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Input file:** {input_file}\n")
        f.write(f"**Input size:** {len(text):,} chars\n")
        if total_tokens:
            f.write(f"**Estimated input tokens:** {total_tokens:,}\n")
        f.write(f"**Output size:** {len(result.stdout):,} chars\n")
        f.write(f"**Processing time:** {elapsed_time:.2f} seconds\n\n")
        f.write("---\n\n")
        f.write(result.stdout)
    
    print(f"\n✓ Results written to: {output_file}")
    print(f"  Input: {len(text):,} chars ({total_tokens:,} tokens)")
    print(f"  Output: {len(result.stdout):,} chars")
    print(f"  Time: {elapsed_time:.2f}s")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else "small.jsonl"
    main(input_file)
