#!/usr/bin/env python3
"""
Analyze Claude conversation history to extract significant decisions, mistakes, and milestones.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from tqdm import tqdm
import tiktoken
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Constants
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GEMINI_MODEL = "gemini-2.5-flash"

# Pricing for Gemini 2.5 Flash (July 2025)
PRICE_PER_M_INPUT = 0.30
PRICE_PER_M_OUTPUT = 2.50

# We don't know how long a report will be 
# but even fairly long ones are only 6k or so so let's be conservative
NOMINAL_REPORT_TOKEN_COUNT = 10_000

MAX_OUTPUT_TOKENS = 65_535  # Conservative estimate for output
ANALYSIS_PROMPT = """Analyze this Claude conversation history and identify:

1. **Significant Decisions**: Key choices made during the project development
2. **Mistakes**: Errors, incorrect approaches, or issues that needed fixing
3. **Milestones**: Important achievements or completed features
4. **Timeline**: A chronological overview of the project's progression

Format the output as a Markdown document with clear sections for each category. 
Include specific examples and quotes where relevant. Include important dates and times.
Be concise but thorough."""

CONSOLIDATION_PROMPT = """Consolidate these subreports into one single final report. 
Merge all decisions, mistakes, milestones, and timeline entries from all subreports.
Remove any duplicates and organize chronologically where appropriate.
Maintain the same section structure: Significant Decisions, Mistakes, Milestones, and Timeline."""

DIFFERENTIAL_CONSOLIDATION_PROMPT = """Consolidate this previous report with this new report, preserving timelines.
The first part is the previous full report. The second part contains new conversations since the last run.
Merge all content appropriately:
- Add new decisions, mistakes, and milestones to existing sections
- Extend the timeline with new events
- Remove any duplicates
- Maintain chronological order where appropriate
Keep the same section structure: Significant Decisions, Mistakes, Milestones, and Timeline."""

METADATA_MARKER = "<!-- Last run:"


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


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    size_kb = size_bytes / 1024
    if size_kb < 100:
        return f"{size_kb:.1f}KB"
    else:
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f}MB"


def format_token_count(tokens: int) -> str:
    """Format token count in human-readable form."""
    if tokens < 1000:
        return f"{tokens} tokens"
    elif tokens < 1000000:
        return f"{tokens/1000:.1f}k tokens"
    else:
        return f"{tokens/1000000:.1f}M tokens"


def estimate_cost(input_tokens: int, max_output_tokens: int = MAX_OUTPUT_TOKENS) -> float:
    """Estimate worst-case cost for analyzing the project."""
    input_cost = (input_tokens / 1_000_000) * PRICE_PER_M_INPUT
    output_cost = (max_output_tokens / 1_000_000) * PRICE_PER_M_OUTPUT
    return input_cost + output_cost


def calculate_project_stats(project_dir: Path) -> Tuple[int, int]:
    """Calculate total size and approximate token count for a project."""
    total_size = 0
    total_tokens = 0
    
    # Use cl100k_base encoding (GPT-4 encoding)
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except:
        encoding = None
    
    for file_path in project_dir.glob("*.jsonl"):
        # Get file size
        total_size += file_path.stat().st_size
        
        # Estimate tokens if encoding available
        if encoding:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    total_tokens += len(encoding.encode(content))
            except:
                pass  # Skip files that can't be read
    
    return total_size, total_tokens


def list_all_projects() -> List[Tuple[str, str, Path, int, int]]:
    """List all Claude projects with their human-friendly names, sizes, and token counts."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return []
    
    projects = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith("-"):
            munged_name = project_dir.name
            friendly_name = get_human_friendly_name(munged_name)
            size_bytes, token_count = calculate_project_stats(project_dir)
            projects.append((friendly_name, munged_name, project_dir, size_bytes, token_count))
    
    return sorted(projects, key=lambda x: x[0].lower())


def find_project_by_name(name: str) -> Optional[Tuple[str, Path]]:
    """Find a project by human-friendly name or path."""
    projects = list_all_projects()
    
    # First try exact match on friendly name (case-insensitive)
    for friendly_name, munged_name, project_dir, _, _ in projects:
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


def get_last_run_date(report_file: Path) -> Optional[datetime]:
    """Extract the last run date from an existing report."""
    if not report_file.exists():
        return None
    
    try:
        with open(report_file, 'r') as f:
            # Read from the end of file
            f.seek(0, 2)  # Go to end
            file_size = f.tell()
            # Read last 200 bytes or whole file if smaller
            f.seek(max(0, file_size - 200))
            tail = f.read()
            
            # Look for metadata marker
            if METADATA_MARKER in tail:
                # Extract date after marker
                start = tail.find(METADATA_MARKER) + len(METADATA_MARKER)
                end = tail.find(" -->", start)
                if end > start:
                    date_str = tail[start:end].strip()
                    return datetime.fromisoformat(date_str)
    except Exception as e:
        print(f"Warning: Could not read last run date: {e}")
    
    return None


def read_jsonl_files(project_dir: Path, since_date: Optional[datetime] = None) -> str:
    """Read and concatenate all JSONL files in the project directory.
    
    If since_date is provided, only include:
    - Files created after since_date
    - Lines from existing files with timestamps after since_date
    """
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    jsonl_files = list(project_dir.glob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No JSONL files found in: {project_dir}")
    
    all_content = []
    files_to_process = []
    
    if since_date:
        print(f"\nDifferential update mode: Processing changes since {since_date.isoformat()}")
        for file_path in jsonl_files:
            stat = file_path.stat()
            # Include if created after last run
            if datetime.fromtimestamp(stat.st_ctime) > since_date:
                files_to_process.append((file_path, "new"))
            # Or if modified after last run (might contain new conversations)
            elif datetime.fromtimestamp(stat.st_mtime) > since_date:
                files_to_process.append((file_path, "partial"))
        
        if not files_to_process:
            print("No new or modified files since last run.")
            return ""
        
        print(f"Found {len([f for f, t in files_to_process if t == 'new'])} new files and "
              f"{len([f for f, t in files_to_process if t == 'partial'])} modified files")
    else:
        files_to_process = [(f, "all") for f in jsonl_files]
        print(f"\nFull analysis mode: Reading {len(jsonl_files)} JSONL files...")
    
    for file_path, process_type in tqdm(sorted(files_to_process), desc="Files", unit="file"):
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
            # For partial files, pre-filter lines by timestamp
            if process_type == "partial" and since_date:
                filtered_lines = []
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if 'timestamp' in data:
                                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                                if timestamp > since_date:
                                    filtered_lines.append(line)
                            else:
                                # Include lines without timestamps in partial mode
                                filtered_lines.append(line)
                        except (json.JSONDecodeError, ValueError):
                            pass
                lines = filtered_lines
                
                if not lines:
                    continue  # Skip if no new lines in this file
            
            for line in tqdm(lines, desc=f"Processing {file_path.name}", unit="line", leave=False):
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
                        pass  # Silently skip invalid lines
    
    return "\n".join(all_content)


def chunk_content(content: str, max_chunk_size: int = 1024 * 1024) -> List[str]:
    """Split content into chunks smaller than max_chunk_size, respecting line boundaries."""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    print(f"\nChunking {len(lines)} lines into ~{max_chunk_size/(1024*1024):.1f}MB chunks...")
    
    for line in tqdm(lines, desc="Chunking", unit="line"):
        line_size = len(line.encode('utf-8')) + 1  # +1 for newline
        
        # If adding this line would exceed the limit, save current chunk
        if current_size + line_size > max_chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        # Add line to current chunk
        current_chunk.append(line)
        current_size += line_size
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks


def analyze_chunk_with_gemini(content: str, chunk_num: int, total_chunks: int) -> str:
    """Send a chunk to Gemini for analysis."""
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY environment variable")
    
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    response = client.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": f"This is chunk {chunk_num} of {total_chunks}. Analyze this portion of the conversation:\n\n{content}"}
        ],
        temperature=0.0
    )
    
    return response.choices[0].message.content


def consolidate_reports(subreports: List[str]) -> str:
    """Consolidate multiple subreports into a final report."""
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY environment variable")
    
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # Combine all subreports
    combined_content = "\n\n---SUBREPORT BOUNDARY---\n\n".join(subreports)
    
    print("\nConsolidating subreports into final report...")
    
    response = client.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[
            {"role": "system", "content": CONSOLIDATION_PROMPT},
            {"role": "user", "content": combined_content}
        ],
        temperature=0.0
    )
    
    return response.choices[0].message.content


def select_project_interactive() -> Tuple[str, Path]:
    """Show list of projects and let user select one."""
    console = Console()
    
    # Show progress while calculating
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Calculating project sizes and estimating token count...", total=None)
        projects = list_all_projects()
        progress.stop()
    
    if not projects:
        console.print("[red]No Claude projects found in ~/.claude/projects/[/red]")
        sys.exit(1)
    
    # Create rich table with more readable colors
    table = Table(title="Available Claude Projects", show_lines=True)
    table.add_column("#", style="bright_cyan", justify="right")
    table.add_column("Project Name", style="bright_green")
    table.add_column("Size", style="bright_blue", justify="right")
    table.add_column("Tokens", style="bright_yellow", justify="right")
    table.add_column("Est. Cost", style="bright_magenta", justify="right")
    
    # Add rows with cost estimates
    for i, (friendly_name, munged_name, _, size_bytes, token_count) in enumerate(projects, 1):
        size_str = format_file_size(size_bytes)
        token_str = format_token_count(token_count)
        cost = estimate_cost(token_count)
        cost_str = f"${cost:.2f}"
        
        table.add_row(
            str(i),
            friendly_name,
            size_str,
            token_str,
            cost_str
        )
    
    console.print("\n")
    console.print(table)
    console.print(f"\n[dim]Pricing: ${PRICE_PER_M_INPUT:.2f}/M input tokens, ${PRICE_PER_M_OUTPUT:.2f}/M output tokens (max {MAX_OUTPUT_TOKENS:,} output)[/dim]")
    
    while True:
        try:
            choice = console.input("\n[bold]Select a project number (or 'q' to quit):[/bold] ")
            if choice.lower() == 'q':
                sys.exit(0)
            
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                _, munged_name, project_dir, _, _ = projects[idx]
                return (munged_name, project_dir)
            else:
                console.print(f"[red]Please enter a number between 1 and {len(projects)}[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")


def main():
    parser = argparse.ArgumentParser(description="Analyze Claude conversation history")
    parser.add_argument("project", nargs="?", help="Project name or path (optional, shows interactive list if not provided)")
    parser.add_argument("--output", "-o", help="Output file name (default: analysis_<project_name>.md)")
    args = parser.parse_args()
    
    if not args.project:
        # No argument provided - show interactive selection
        munged_path, project_dir = select_project_interactive()
        project_path = get_full_path_from_munged(munged_path)
    else:
        # Argument provided - could be path or friendly name
        arg = args.project
        
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
        # Check for existing report and last run date
        if args.output:
            output_file = args.output
        else:
            output_file = f"analysis_{get_human_friendly_name(munged_path).replace(' ', '_').lower()}.md"
        output_path = Path(output_file)
        last_run_date = get_last_run_date(output_path)
        is_differential = last_run_date is not None
        
        # Read JSONL files (differential or full)
        content = read_jsonl_files(project_dir, since_date=last_run_date)
        
        if is_differential and not content:
            print("\nNo new conversations since last run. Report is up to date.")
            return
        
        print(f"\nTotal content size: {len(content)} characters")
        
        # Get current run time
        current_run_time = datetime.now()
        
        if is_differential:
            # Differential update mode
            print("\nPerforming differential update...")
            
            # Read existing report (without metadata line)
            with open(output_path, 'r') as f:
                existing_report = f.read()
                # Remove metadata line if present
                if METADATA_MARKER in existing_report:
                    metadata_start = existing_report.rfind(METADATA_MARKER)
                    existing_report = existing_report[:metadata_start].rstrip()
            
            # Analyze new content
            if len(content) > 1024 * 1024:
                # Chunk if needed
                chunks = chunk_content(content)
                print(f"New content split into {len(chunks)} chunks for analysis.")
                subreports = []
                with tqdm(total=len(chunks), desc="Analyzing new chunks", unit="chunk") as pbar:
                    for i, chunk in enumerate(chunks, 1):
                        chunk_size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
                        pbar.set_description(f"Analyzing chunk {i}/{len(chunks)} ({chunk_size_mb:.2f}MB)")
                        
                        subreport = analyze_chunk_with_gemini(chunk, i, len(chunks))
                        subreports.append(subreport)
                        pbar.update(1)
                
                # Consolidate new content reports
                new_analysis = consolidate_reports(subreports)
            else:
                # Single chunk for new content
                print("Analyzing new conversations...")
                new_analysis = analyze_chunk_with_gemini(content, 1, 1)
            
            # Consolidate with existing report
            print("\nMerging with existing report...")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Please set GEMINI_API_KEY environment variable")
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            
            combined_content = f"PREVIOUS REPORT:\n\n{existing_report}\n\n---NEW CONVERSATIONS ANALYSIS---\n\n{new_analysis}"
            
            response = client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=[
                    {"role": "system", "content": DIFFERENTIAL_CONSOLIDATION_PROMPT},
                    {"role": "user", "content": combined_content}
                ],
                temperature=0.0
            )
            
            analysis = response.choices[0].message.content
            
        else:
            # Full analysis mode (same as before)
            chunks = chunk_content(content)
            num_chunks = len(chunks)
            
            if num_chunks == 1:
                print("Content fits in a single chunk, analyzing directly...")
                analysis = analyze_chunk_with_gemini(chunks[0], 1, 1)
                subreports = [analysis]
            else:
                print(f"\nContent split into {num_chunks} chunks for analysis.")
                print(f"Note: This may take several minutes for large projects.\n")
                
                subreports = []
                with tqdm(total=num_chunks, desc="Analyzing chunks", unit="chunk") as pbar:
                    for i, chunk in enumerate(chunks, 1):
                        chunk_size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
                        pbar.set_description(f"Analyzing chunk {i}/{num_chunks} ({chunk_size_mb:.2f}MB)")
                        
                        subreport = analyze_chunk_with_gemini(chunk, i, num_chunks)
                        
                        # Save subreport
                        if args.output:
                            # Use custom output base name for subreports
                            base_name = Path(args.output).stem
                            subreport_file = f"subreport_{base_name}_chunk{i}.md"
                        else:
                            subreport_file = f"subreport_{get_human_friendly_name(munged_path).replace(' ', '_').lower()}_chunk{i}.md"
                        with open(subreport_file, 'w') as f:
                            f.write(f"# Subreport {i}/{num_chunks}: {get_human_friendly_name(munged_path)}\n\n")
                            f.write(subreport)
                        
                        subreports.append(subreport)
                        pbar.update(1)
                
                # Consolidate reports
                analysis = consolidate_reports(subreports)
        
        # Save the final analysis with metadata
        with open(output_file, 'w') as f:
            f.write(f"# Claude Project Analysis: {get_human_friendly_name(munged_path)}\n\n")
            f.write(f"**Full Path**: {project_path}\n\n")
            if is_differential:
                f.write(f"**Last Updated**: {current_run_time.isoformat()}\n\n")
                f.write(f"**Update Type**: Differential (changes since {last_run_date.isoformat()})\n\n")
            else:
                if not is_differential and num_chunks > 1:
                    f.write(f"**Note**: This analysis was generated from {num_chunks} chunks. See subreport files for detailed chunk analyses.\n\n")
            f.write(analysis)
            f.write(f"\n\n{METADATA_MARKER} {current_run_time.isoformat()} -->")
        
        if is_differential:
            print(f"\nDifferential update completed. Report saved to: {output_file}")
        else:
            print(f"\nFull analysis completed. Report saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()