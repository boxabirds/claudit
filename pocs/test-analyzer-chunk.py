#!/usr/bin/env python3
"""
Test exactly what the analyzer does for a chunk
"""

import subprocess
import os
import json
from pathlib import Path

# Get the actual prompt from RulesAnalyzer
ANALYSIS_PROMPT = """You are an expert corporate performance psychologist. You have deep insight into the human psyche. Your job is to analyse the provided conversations between the AI assistant and the User to produce a list of up to 100 incidents in the conversation where the assistant upset, angered, frustrated, or confused the user due to not meeting expectations, being unprofessional, lazy, ambiguous, whimsical, lacking tenacity, incompetent, or stupid. The goal is collating a list of corrective and preventative rules for the assistant to avoid having them happen again. 

Format each incident as:
- What happened: [specific behavior]
- Rule: [corrective action]
- Example: [quote from conversation if applicable]

Group rules into two sections:

1. **CLAUDE.md Candidates**: Concise, unambiguous rules suitable for system prompts

2. **Claude Hooks Candidates**: Rules that could be automated with hooks. Present as a table with columns:
   | Proposed Hook | Example It Prevents | Event Type | Matcher Pattern | Command |
   |---------------|-------------------|------------|-----------------|---------|
   | Verify API docs before implementation | Assistant tried using an API without looking at docs | PreToolUse | tool_name="Write" or tool_name="MultiEdit" | grep -q "api" $CLAUDE_FILE_PATHS && echo "Check API docs first" |
   | Enforce web codecs usage | Assistant chose "simpler" method instead of agreed web codecs | PostToolUse | file_paths=["*.js", "*.ts"] | grep -q "video\\|audio" $CLAUDE_TOOL_OUTPUT && ! grep -q "webcodecs" && echo "Use Web Codecs API as agreed" |

Research Claude hooks documentation to ensure hook configurations are valid and follow best practices."""

# Read a small sample from an actual project
project_dir = Path.home() / ".claude/projects/-Users-julian-expts-agent-tools"
jsonl_files = list(project_dir.glob("*.jsonl"))

if not jsonl_files:
    print("No JSONL files found!")
    exit(1)

# Read first 100 lines as sample
content_lines = []
with open(jsonl_files[0], 'r') as f:
    for i, line in enumerate(f):
        if i >= 100:
            break
        if line.strip():
            try:
                data = json.loads(line)
                # Just keep the message content for testing
                if 'message' in data:
                    content_lines.append(json.dumps({'message': data['message']}))
            except:
                pass

sample_content = '\n'.join(content_lines)
print(f"Sample content: {len(sample_content)} chars")

# Build the full prompt like the analyzer does
full_prompt = f"{ANALYSIS_PROMPT}\n\nThis is chunk 1 of 1. Analyze this portion of the conversation:\n\n{sample_content}"
print(f"Full prompt: {len(full_prompt)} chars")

# Run gemini with the exact same pattern
cmd = ["gemini", "-m", "gemini-2.5-flash"]
env = os.environ.copy()
if 'GOOGLE_APPLICATION_CREDENTIALS' in env:
    del env['GOOGLE_APPLICATION_CREDENTIALS']

print(f"\nRunning: {' '.join(cmd)}")
print("Sending prompt via stdin...")

try:
    result = subprocess.run(
        cmd,
        input=full_prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=30
    )
    
    print(f"\n✓ Exit code: {result.returncode}")
    print(f"✓ Stdout length: {len(result.stdout)} chars")
    if result.stdout:
        print(f"✓ Output preview:\n{result.stdout[:500]}...")
    if result.stderr:
        print(f"⚠️ Stderr: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("✗ TIMEOUT after 30 seconds!")
except Exception as e:
    print(f"✗ Error: {e}")