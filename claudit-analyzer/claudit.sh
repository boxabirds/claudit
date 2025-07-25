#!/usr/bin/env bash
# Wrapper script for Claude conversation analyzer

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: uv venv -p 3.12"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Warning: GEMINI_API_KEY environment variable not set!"
    echo "Please export GEMINI_API_KEY=your_api_key_here"
    echo ""
fi

# Run the analyzer with all arguments passed through
# No timeout - let it run as long as needed
exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/analyze_claude_history_v2.py" "$@"