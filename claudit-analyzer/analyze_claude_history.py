#!/usr/bin/env python3
"""
Analyze Claude conversation history to extract significant decisions, mistakes, and milestones.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI

# Constants
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GEMINI_MODEL = "gemini-2.5-flash"
ANALYSIS_PROMPT = """Analyze this Claude conversation history and identify:

1. **Significant Decisions**: Key choices made during the project development
2. **Mistakes**: Errors, incorrect approaches, or issues that needed fixing
3. **Milestones**: Important achievements or completed features

Format the output as a Markdown document with clear sections for each category. 
Include specific examples and quotes where relevant.
Be concise but thorough."""


def munge_project_path(project_path: str) -> str:
    """Convert a project path to the Claude folder name format."""
    # Replace slashes with dashes
    return project_path.replace("/", "-")


def get_human_friendly_name(munged_path: str) -> str:
    """Extract human-friendly name from munged path."""
    # The munged path looks like -Users-julian-expts-n8n-fly
    # We need to find the leaf folder, which in the original path was n8n-fly
    # Strategy: split by - and reconstruct, looking for the actual folder structure
    
    # Remove leading dash
    if munged_path.startswith("-"):
        munged_path = munged_path[1:]
    
    # For now, we'll assume the leaf folder is everything after 'expts-'
    # This is a heuristic that works for the given examples
    parts = munged_path.split("-")
    
    # Find where 'expts' appears and take everything after it
    try:
        expts_idx = parts.index("expts")
        if expts_idx < len(parts) - 1:
            # Everything after 'expts' is the project path
            leaf_parts = parts[expts_idx + 1:]
            leaf_name = "-".join(leaf_parts)
        else:
            # Fallback: just use the last part
            leaf_name = parts[-1] if parts else "unknown"
    except ValueError:
        # 'expts' not found, just use the last component
        leaf_name = parts[-1] if parts else "unknown"
    
    # Replace dashes with spaces and capitalize each word
    words = leaf_name.replace("-", " ").split()
    return " ".join(word.capitalize() for word in words) if words else "Unknown Project"


def get_full_path_from_munged(munged_path: str) -> str:
    """Convert munged path back to full path (best guess)."""
    # Remove leading dash and replace dashes with slashes
    return munged_path.lstrip("-").replace("-", "/")


def list_all_projects() -> List[Tuple[str, str, Path]]:
    """List all Claude projects with their human-friendly names."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return []
    
    projects = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith("-"):
            munged_name = project_dir.name
            friendly_name = get_human_friendly_name(munged_name)
            projects.append((friendly_name, munged_name, project_dir))
    
    return sorted(projects, key=lambda x: x[0].lower())


def find_project_by_name(name: str) -> Optional[Tuple[str, Path]]:
    """Find a project by human-friendly name or path."""
    projects = list_all_projects()
    
    # First try exact match on friendly name (case-insensitive)
    for friendly_name, munged_name, project_dir in projects:
        if friendly_name.lower() == name.lower():
            return (munged_name, project_dir)
    
    # If not found, try as a path
    if "/" in name or name.startswith("-"):
        munged = munge_project_path(name) if "/" in name else name
        project_dir = CLAUDE_PROJECTS_DIR / munged
        if project_dir.exists():
            return (munged, project_dir)
    
    return None


def check_ambiguous_paths(munged_path: str) -> List[str]:
    """Check if multiple original paths could map to the same munged path."""
    # This is a simple check - in reality, we'd need to scan all possible paths
    # For now, we'll just check if the munged path contains multiple consecutive dashes
    if "--" in munged_path:
        return ["Path might be ambiguous due to consecutive dashes"]
    return []


def read_jsonl_files(project_dir: Path) -> str:
    """Read and concatenate all JSONL files in the project directory."""
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    jsonl_files = list(project_dir.glob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No JSONL files found in: {project_dir}")
    
    all_content = []
    for file_path in sorted(jsonl_files):
        print(f"Reading: {file_path}")
        with open(file_path, 'r') as f:
            for line in f:
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
                        
                        # Only add if we have meaningful content
                        if filtered_data and ('message' in filtered_data or 'type' in filtered_data):
                            all_content.append(json.dumps(filtered_data))
                    except json.JSONDecodeError:
                        print(f"Warning: Skipping invalid JSON line in {file_path}")
    
    return "\n".join(all_content)


def analyze_with_gemini(content: str) -> str:
    """Send content to Gemini for analysis."""
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY environment variable")
    
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    print(f"Sending {len(content)} characters to Gemini...")
    
    response = client.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": content}
        ],
        temperature=0.0
    )
    
    return response.choices[0].message.content


def select_project_interactive() -> Tuple[str, Path]:
    """Show list of projects and let user select one."""
    projects = list_all_projects()
    
    if not projects:
        print("No Claude projects found in ~/.claude/projects/")
        sys.exit(1)
    
    print("\nAvailable Claude projects:")
    print("-" * 50)
    for i, (friendly_name, munged_name, _) in enumerate(projects, 1):
        full_path = get_full_path_from_munged(munged_name)
        print(f"{i}. {friendly_name} ({full_path})")
    print("-" * 50)
    
    while True:
        try:
            choice = input("\nSelect a project number (or 'q' to quit): ")
            if choice.lower() == 'q':
                sys.exit(0)
            
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                _, munged_name, project_dir = projects[idx]
                return (munged_name, project_dir)
            else:
                print(f"Please enter a number between 1 and {len(projects)}")
        except ValueError:
            print("Please enter a valid number")


def main():
    if len(sys.argv) == 1:
        # No argument provided - show interactive selection
        munged_path, project_dir = select_project_interactive()
        project_path = get_full_path_from_munged(munged_path)
    else:
        # Argument provided - could be path or friendly name
        arg = sys.argv[1]
        
        # Try to find by friendly name or path
        result = find_project_by_name(arg)
        if result:
            munged_path, project_dir = result
            project_path = get_full_path_from_munged(munged_path) if "/" not in arg else arg
        else:
            # Fallback to treating it as a path
            project_path = arg
            munged_path = munge_project_path(project_path)
            project_dir = CLAUDE_PROJECTS_DIR / munged_path
            
            if not project_dir.exists():
                print(f"Error: Project not found: {arg}")
                print("\nTry running without arguments to see available projects.")
                sys.exit(1)
    
    # Check for ambiguity
    ambiguities = check_ambiguous_paths(munged_path)
    if ambiguities:
        print("WARNING: Path might be ambiguous!")
        print("The following project paths would map to the same folder:")
        for amb in ambiguities:
            print(f"  - {amb}")
        print("\nPlease rename your projects to avoid ambiguity.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print(f"\nProject: {get_human_friendly_name(munged_path)}")
    print(f"Full path: {project_path}")
    print(f"Looking for files in: {project_dir}")
    
    try:
        # Read all JSONL files
        content = read_jsonl_files(project_dir)
        print(f"\nTotal content size: {len(content)} characters")
        
        # Analyze with Gemini
        analysis = analyze_with_gemini(content)
        
        # Save the analysis
        output_file = f"analysis_{get_human_friendly_name(munged_path).replace(' ', '_').lower()}.md"
        with open(output_file, 'w') as f:
            f.write(f"# Claude Project Analysis: {get_human_friendly_name(munged_path)}\n\n")
            f.write(f"**Full Path**: {project_path}\n\n")
            f.write(analysis)
        
        print(f"\nAnalysis saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()