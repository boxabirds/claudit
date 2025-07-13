#!/usr/bin/env python3
"""
Analyze Claude conversation history to extract significant decisions, mistakes, and milestones,
or to identify behavioral rules for improvement.
"""

import threading
import argparse
import json
import os
import sys
import subprocess
import shutil
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI
from tqdm import tqdm
import tiktoken
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Constants
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GEMINI_MODEL = "gemini-2.5-flash"

# Constants for retry mechanism
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 5
GEMINI_CLI_TIMEOUT = 120  # seconds - increased to account for directory scanning overhead

# Pricing for Gemini 2.5 Flash (July 2025)
PRICE_PER_M_INPUT = 0.30
PRICE_PER_M_OUTPUT = 2.50

# We don't know how long a report will be 
# but even fairly long ones are only 6k or so so let's be conservative
NOMINAL_REPORT_TOKEN_COUNT = 10_000

# Minimal 1x1 transparent PNG as base64 placeholder
PLACEHOLDER_IMAGE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

MAX_OUTPUT_TOKENS = 65_535  # Conservative estimate for output

METADATA_MARKER = "<!-- Last run:"
CACHE_MARKER = "<!-- Cache updated:"
PROJECTS_CACHE_FILE = "projects_cache.json"

class SubProcessExecutionResult:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
    
    # take stderror raw text and figure out what the error was
    


class ConversationAnalyzer(ABC):
    """Abstract base class for analyzing Claude conversations."""
    
    def __init__(self, args):
        self.args = args
        self.console = Console()
        self._gemini_model_override_active = False
    
    @abstractmethod
    def get_analysis_prompt(self) -> str:
        """Return the main analysis prompt."""
        pass
    
    @abstractmethod
    def get_consolidation_prompt(self) -> str:
        """Return the consolidation prompt."""
        pass
    
    @abstractmethod
    def get_differential_consolidation_prompt(self) -> str:
        """Return the differential consolidation prompt."""
        pass
    
    @abstractmethod
    def get_output_prefix(self) -> str:
        """Return the prefix for output files."""
        pass
    
    @abstractmethod
    def format_final_report(self, content: str, project_name: str, 
                          project_path: str, **kwargs) -> str:
        """Format the final report with appropriate headers."""
        pass
    
    def check_google_credentials(self):
        """Log if GOOGLE_APPLICATION_CREDENTIALS is set (always ignored for CLI)."""
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            self.console.print("[dim]Note: GOOGLE_APPLICATION_CREDENTIALS will be unset for Gemini CLI calls.[/dim]")
    
    def get_gemini_client(self) -> OpenAI:
        """Get OpenAI client configured for Gemini."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Please set GEMINI_API_KEY environment variable")
        
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        return OpenAI(api_key=api_key, base_url=base_url)
    
    
    def munge_project_path(self, project_path: str) -> str:
        """Convert a project path to the Claude folder name format."""
        return project_path.replace("/", "-")
    
    def get_human_friendly_name(self, munged_path: str) -> str:
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
    
    def get_full_path_from_munged(self, munged_path: str) -> str:
        """Convert munged path back to full path (best guess)."""
        # Remove leading dash and replace dashes with slashes
        return munged_path.lstrip("-").replace("-", "/")
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable form."""
        size_kb = size_bytes / 1024
        if size_kb < 100:
            return f"{size_kb:.1f}KB"
        else:
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.1f}MB"
    
    def format_token_count(self, tokens: int) -> str:
        """Format token count in human-readable form."""
        if tokens < 1000:
            return f"{tokens} tokens"
        elif tokens < 1000000:
            return f"{tokens/1000:.1f}k tokens"
        else:
            return f"{tokens/1000000:.1f}M tokens"
    
    def estimate_cost(self, input_tokens: int, max_output_tokens: int = MAX_OUTPUT_TOKENS) -> float:
        """Estimate worst-case cost for analyzing the project."""
        input_cost = (input_tokens / 1_000_000) * PRICE_PER_M_INPUT
        output_cost = (max_output_tokens / 1_000_000) * PRICE_PER_M_OUTPUT
        return input_cost + output_cost
    
    def get_project_mtime(self, project_dir: Path) -> float:
        """Get the most recent modification time of any file in the project."""
        mtime = 0.0
        for file_path in project_dir.glob("*.jsonl"):
            file_mtime = file_path.stat().st_mtime
            if file_mtime > mtime:
                mtime = file_mtime
        return mtime
    
    def load_projects_cache(self) -> Dict[str, Any]:
        """Load the projects cache from disk."""
        # Use output directory for cache file
        cache_file = Path(self.args.out_dir if hasattr(self, 'args') else 'reports') / PROJECTS_CACHE_FILE
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    # Read JSON data, ignoring any trailing comment
                    content = f.read()
                    # Remove the cache marker comment if present
                    if CACHE_MARKER in content:
                        content = content[:content.find(CACHE_MARKER)].strip()
                    return json.loads(content) if content else {}
            except Exception as e:
                print(f"[yellow]Warning: Could not load projects cache: {e}[/yellow]")
                return {}
        return {}
    
    def save_projects_cache(self, cache: Dict[str, Any]):
        """Save the projects cache to disk with timestamp."""
        # Use output directory for cache file
        output_dir = Path(self.args.out_dir if hasattr(self, 'args') else 'reports')
        output_dir.mkdir(exist_ok=True)
        cache_file = output_dir / PROJECTS_CACHE_FILE
        
        try:
            # Write cache data with timestamp comment
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
                f.write(f"\n{CACHE_MARKER} {datetime.now().isoformat()} -->")
        except Exception as e:
            print(f"[yellow]Warning: Could not save projects cache: {e}[/yellow]")
    
    def calculate_project_stats(self, project_dir: Path, cache: Dict[str, Any] = None) -> Tuple[int, int]:
        """Calculate total size and approximate token count for a project."""
        # Check cache first
        project_name = project_dir.name
        current_mtime = self.get_project_mtime(project_dir)
        
        if cache and project_name in cache:
            cached_data = cache[project_name]
            if cached_data.get('mtime', 0) >= current_mtime:
                # Cache is still valid
                return cached_data['size'], cached_data['tokens']
        
        # Calculate fresh stats
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
        
        # Update cache
        if cache is not None:
            cache[project_name] = {
                'size': total_size,
                'tokens': total_tokens,
                'mtime': current_mtime
            }
        
        return total_size, total_tokens
    
    def list_all_projects(self) -> List[Tuple[str, str, Path, int, int]]:
        """List all Claude projects with their human-friendly names, sizes, and token counts."""
        if not CLAUDE_PROJECTS_DIR.exists():
            return []
        
        # Load cache
        cache = self.load_projects_cache()
        cache_updated = False
        
        projects = []
        for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
            if project_dir.is_dir() and project_dir.name.startswith("-"):
                munged_name = project_dir.name
                friendly_name = self.get_human_friendly_name(munged_name)
                
                # Calculate stats (will use cache if valid)
                old_cache_size = len(cache)
                size_bytes, token_count = self.calculate_project_stats(project_dir, cache)
                if len(cache) > old_cache_size or (munged_name in cache and 
                    cache[munged_name].get('size') != size_bytes):
                    cache_updated = True
                
                projects.append((friendly_name, munged_name, project_dir, size_bytes, token_count))
        
        # Save cache if updated
        if cache_updated:
            self.save_projects_cache(cache)
        
        return sorted(projects, key=lambda x: x[0].lower())
    
    def find_project_by_name(self, name: str) -> Optional[Tuple[str, Path]]:
        """Find a project by human-friendly name or path."""
        projects = self.list_all_projects()
        
        # First try exact match on friendly name (case-insensitive)
        for friendly_name, munged_name, project_dir, _, _ in projects:
            if friendly_name.lower() == name.lower():
                return (munged_name, project_dir)
        
        # If not found, try as a path
        if "/" in name or name.startswith("-"):
            munged = self.munge_project_path(name) if "/" in name else name
            project_dir = CLAUDE_PROJECTS_DIR / munged
            if project_dir.exists():
                return (munged, project_dir)
        
        return None
    
    def check_ambiguous_paths(self, munged_path: str) -> List[str]:
        """Check if multiple original paths could map to the same munged path."""
        # This is a simple check - in reality, we'd need to scan all possible paths
        # For now, we'll just check if the munged path contains multiple consecutive dashes
        if "--" in munged_path:
            return ["Path might be ambiguous due to consecutive dashes"]
        return []
    
    def strip_base64_images(self, content: Any) -> Any:
        """Recursively strip base64 images from content and replace with placeholder."""
        if isinstance(content, str):
            # Check if this is a base64 image data URL
            if content.startswith("data:image/") and ";base64," in content:
                # Extract the image type for the placeholder message
                image_type = content.split(";")[0].split("/")[1]
                return f"[IMAGE: {image_type} removed]"
            return content
        elif isinstance(content, list):
            return [self.strip_base64_images(item) for item in content]
        elif isinstance(content, dict):
            return {key: self.strip_base64_images(value) for key, value in content.items()}
        else:
            return content
    
    def check_gemini_cli(self) -> bool:
        """Check if gemini CLI is installed and available."""
        return shutil.which("gemini") is not None
    
    
    def choose_analysis_method(self) -> str:
        """Automatically choose the best analysis method."""
        if self.args.force_gemini_cli:
            return "cli"
        if self.args.force_api:
            return "api"
        
        has_gemini_cli = self.check_gemini_cli()
        has_api_key = os.getenv("GEMINI_API_KEY") is not None
        
        # Prefer CLI if available (free tier)
        if has_gemini_cli:
            self.console.print("[green]Using Gemini CLI (free tier)[/green]")
            return "cli"
        
        # Fall back to API if available
        if has_api_key:
            self.console.print("[blue]Using Gemini API[/blue]")
            return "api"
        
        # No options available - offer to install CLI
        self.console.print("\n[red]No analysis method available.[/red]")
        self.console.print("\nGemini CLI is not installed. With Gemini CLI, you can:")
        self.console.print("• Use the [bold green]free tier[/bold green] (with Google login)")
        self.console.print("• Avoid needing an API key")
        
        self.console.print("\nTo install: [cyan]pip install google-generativeai[/cyan]")
        self.console.print("\nAlternatively, get an API key from: [cyan]https://aistudio.google.com[/cyan]")
        self.console.print("Then: [cyan]export GEMINI_API_KEY=your_key_here[/cyan]")
        sys.exit(1)
    
    def get_last_run_date(self, report_file: Path) -> Optional[datetime]:
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
    
    def read_jsonl_files(self, project_dir: Path, since_date: Optional[datetime] = None) -> str:
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
                                filtered_data['message'] = self.strip_base64_images(data['message'])
                            if 'timestamp' in data:
                                filtered_data['timestamp'] = data['timestamp']
                            if 'children' in data:
                                filtered_data['children'] = self.strip_base64_images(data['children'])
                            
                            # Keep type to understand the structure
                            if 'type' in data:
                                filtered_data['type'] = data['type']
                            
                            # Strip images from toolUseResult if present
                            if 'toolUseResult' in data:
                                filtered_data['toolUseResult'] = self.strip_base64_images(data['toolUseResult'])
                            
                            # Only add if we have meaningful content
                            if filtered_data and ('message' in filtered_data or 'type' in filtered_data):
                                all_content.append(json.dumps(filtered_data))
                        except json.JSONDecodeError:
                            pass  # Silently skip invalid lines
        
        return "\n".join(all_content)
    
    def chunk_content(self, content: str, max_chunk_size: int = 1024 * 1024) -> List[str]:
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
    
    
    def run_analysis_with_gemini_cli(self,  input_text: str, attempt: int) -> tuple[SubProcessExecutionResult,int]:
    
        prompt = self.get_analysis_prompt()
        GEMINI_CLI_CMD = ["gemini", "-m", "gemini-2.5-flash", "-p", prompt]
        print(f"\n[blue]═══ Gemini CLI Call (Attempt {attempt + 1}/{MAX_RETRIES}) ═══[/blue]", flush=True)
        print(f"[dim]Command: {' '.join(GEMINI_CLI_CMD)}[/dim]", flush=True)
        print(f"[dim]Input length: {len(input_text)} characters[/dim]", flush=True)
        
        try:
            # Create a clean environment without GOOGLE_APPLICATION_CREDENTIALS which overrides our 
            # 'normal' Google Login credentials -- and we miss out on the goodie bag that comes with that tier
            # This took hours to figure out. It shouldn't have. 
            clean_env = os.environ.copy()
            clean_env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)            
            print(f"[dim]Environment has {len(clean_env)} vars (removed GOOGLE_APPLICATION_CREDENTIALS)[/dim]", flush=True)

            # Always good to catch performance data. 
            start_time = time.time()
            
            # Use Popen for real-time output -- incredibly hard to figure out what goes on 
            # when running the gemini CLI command otherwise. It becomes an impenetrable black box
            # that causes you hours of misery. Don't repeat my mistakes: Popen is your friend!
            proc = subprocess.Popen(
                GEMINI_CLI_CMD, 
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
            
            # All processes produce output in two places: "standard out" and "standard error"
            # We just merge them. 
            output_lines = []
            error_lines = []
            
            def read_stream(stream, lines, prefix):
                # inline / local functions are pythonic apparently. But in an inner loop? 🤔
                for line in stream:
                    print(f"[{prefix}]: {line}", end='', flush=True)
                    lines.append(line)
            
            # Start threads for reading
            stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, output_lines, "stdout"))
            stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, error_lines, "stderr"))
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait FOREVER 🧙‍♂️ for process to complete
            return_code = proc.wait()
            
            # Wait for threads to finish reading
            stdout_thread.join()
            stderr_thread.join()
            
            elapsed_time = time.time() - start_time
            
            print(f"\n--- Process completed with exit code: {return_code} ---", flush=True)
            print(f"Output length: {len(''.join(output_lines))} chars", flush=True)
            print(f"Processing time: {elapsed_time:.2f}")

            result = SubProcessExecutionResult(return_code, ''.join(output_lines), ''.join(error_lines))
 
    
    def analyze_chunk_with_gemini_cli(self, content: str, chunk_num: int, total_chunks: int) -> str:
        """Analyze a chunk using Gemini CLI."""
        print(f"\n[ENTER] analyze_chunk_with_gemini_cli for chunk {chunk_num}/{total_chunks}", flush=True)
        prompt = self.get_analysis_prompt()
        
        for attempt in range(MAX_RETRIES):
            try:
                # Prepare the full prompt content
                full_prompt = f"This is chunk {chunk_num} of {total_chunks}. Analyze this portion of the conversation:\n\n{content}"
                
                result, execution_time_in_millis = self.run_analysis_with_gemini_cli(full_prompt, attempt)
                
                return result.stdout
            except subprocess.TimeoutExpired as e:
                # Check if it's actually a rate limit disguised as a timeout
                stderr_text = ""
                if hasattr(e, 'stderr') and e.stderr:
                    stderr_text = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                    
                is_rate_limit = "429" in stderr_text or "RESOURCE_EXHAUSTED" in stderr_text or "Quota exceeded" in stderr_text
                
                if is_rate_limit:
                    print(f"\n[yellow]Gemini CLI hit rate limit (detected in timeout).[/yellow]")
                    if "Gemini 2.5 Pro" in stderr_text and not self._gemini_model_override_active:
                        self._gemini_model_override_active = True
                        print(f"[yellow]Switching from Pro to Flash model due to quota limits.[/yellow]")
                else:
                    print(f"\n[yellow]Gemini CLI timed out after {GEMINI_CLI_TIMEOUT} seconds.[/yellow]")
                
                # Show the command that timed out
                print(f"[dim]Command: {' '.join(cmd)}[/dim]")
                print(f"[dim]Attempt {attempt + 1}/{MAX_RETRIES}[/dim]")
                
                # Show partial stderr if available
                if stderr_text:
                    # Extract the most relevant error message
                    if "message" in stderr_text:
                        try:
                            import re
                            match = re.search(r'"message":\s*"([^"]+)"', stderr_text)
                            if match:
                                print(f"[red]Error: {match.group(1)}[/red]")
                        except:
                            pass
                    else:
                        print(f"[dim]Partial error: {stderr_text[:300]}...[/dim]")
                
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                print(f"\nRetrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            except subprocess.CalledProcessError as e:
                if "429" in e.stderr or "RESOURCE_EXHAUSTED" in e.stderr:
                    if not self._gemini_model_override_active:
                        self._gemini_model_override_active = True
                        print("\n[yellow]Rate limit hit. Switching to 'gemini-2.5-flash' model for subsequent calls.[/yellow]")
                    wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    print(f"\nGemini CLI rate limit hit (429). Retrying in {wait_time:.1f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    print(f"\n[red]Gemini CLI error:[/red]")
                    print(f"[red]Exit code: {e.returncode}[/red]")
                    print(f"[red]Error output:[/red]\n{e.stderr}")
                    raise RuntimeError(f"Gemini CLI failed: {e.stderr}")

        raise RuntimeError(f"Gemini CLI failed after {MAX_RETRIES} attempts due to rate limiting.")
    
    def analyze_chunk_with_gemini(self, content: str, chunk_num: int, total_chunks: int, use_cli: bool = False) -> str:
        """Send a chunk to Gemini for analysis."""
        if use_cli:
            result = self.analyze_chunk_with_gemini_cli(content, chunk_num, total_chunks)
            time.sleep(1) # Rate limit to 60 requests/minute
            return result
        
        client = self.get_gemini_client()
        prompt = self.get_analysis_prompt()
        
        response = client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"This is chunk {chunk_num} of {total_chunks}. Analyze this portion of the conversation:\n\n{content}"}
            ],
            temperature=0.0
        )
        time.sleep(1) # Rate limit to 60 requests/minute
        return response.choices[0].message.content or ""
    
    def consolidate_reports_with_cli(self, subreports: List[str]) -> str:
        """Consolidate reports using Gemini CLI."""
        combined_content = "\n\n---SUBREPORT BOUNDARY---\n\n".join(subreports)
        prompt = self.get_consolidation_prompt()
        
        for attempt in range(MAX_RETRIES):
            try:
                # Prepare the full prompt content
                full_prompt = f"{prompt}\n\n{combined_content}"
                
                # Build command with flash model to avoid Pro quota issues
                cmd = ["gemini", "-m", "gemini-2.5-flash"]

                # Use the logging wrapper - pass content directly via stdin
                result = self.run_gemini_cli_with_logging(cmd, full_prompt, attempt)
                
                return result.stdout
            except subprocess.TimeoutExpired as e:
                # Check if it's actually a rate limit disguised as a timeout
                stderr_text = ""
                if hasattr(e, 'stderr') and e.stderr:
                    stderr_text = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                    
                is_rate_limit = "429" in stderr_text or "RESOURCE_EXHAUSTED" in stderr_text or "Quota exceeded" in stderr_text
                
                if is_rate_limit:
                    print(f"\n[yellow]Gemini CLI hit rate limit (detected in timeout).[/yellow]")
                    if "Gemini 2.5 Pro" in stderr_text and not self._gemini_model_override_active:
                        self._gemini_model_override_active = True
                        print(f"[yellow]Switching from Pro to Flash model due to quota limits.[/yellow]")
                else:
                    print(f"\n[yellow]Gemini CLI timed out after {GEMINI_CLI_TIMEOUT} seconds.[/yellow]")
                
                # Show the command that timed out
                print(f"[dim]Command: {' '.join(cmd)}[/dim]")
                print(f"[dim]Attempt {attempt + 1}/{MAX_RETRIES}[/dim]")
                
                # Show partial stderr if available
                if stderr_text:
                    # Extract the most relevant error message
                    if "message" in stderr_text:
                        try:
                            import re
                            match = re.search(r'"message":\s*"([^"]+)"', stderr_text)
                            if match:
                                print(f"[red]Error: {match.group(1)}[/red]")
                        except:
                            pass
                    else:
                        print(f"[dim]Partial error: {stderr_text[:300]}...[/dim]")
                
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                print(f"\nRetrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            except subprocess.CalledProcessError as e:
                if "429" in e.stderr or "RESOURCE_EXHAUSTED" in e.stderr:
                    if not self._gemini_model_override_active:
                        self._gemini_model_override_active = True
                        print("\n[yellow]Rate limit hit. Switching to 'gemini-2.5-flash' model for subsequent calls.[/yellow]")
                    wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                    print(f"\nGemini CLI rate limit hit (429). Retrying in {wait_time:.1f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    print(f"\n[red]Gemini CLI error:[/red]")
                    print(f"[red]Exit code: {e.returncode}[/red]")
                    print(f"[red]Error output:[/red]\n{e.stderr}")
                    raise RuntimeError(f"Gemini CLI failed: {e.stderr}")
        
        raise RuntimeError(f"Gemini CLI failed after {MAX_RETRIES} attempts due to rate limiting.")
    
    def consolidate_reports(self, subreports: List[str], use_cli: bool = False) -> str:
        """Consolidate multiple subreports into a final report."""
        if use_cli:
            result = self.consolidate_reports_with_cli(subreports)
            time.sleep(1) # Rate limit to 60 requests/minute
            return result
        
        client = self.get_gemini_client()
        prompt = self.get_consolidation_prompt()
        
        # Combine all subreports
        combined_content = "\n\n---SUBREPORT BOUNDARY---\n\n".join(subreports)
        
        print("\nConsolidating subreports into final report...")
        
        response = client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": combined_content}
            ],
            temperature=0.0
        )
        time.sleep(1) # Rate limit to 60 requests/minute
        return response.choices[0].message.content or ""
    
    def select_project_interactive(self, show_costs: bool = True) -> Tuple[str, Path]:
        """Show list of projects and let user select one."""
        if self.args.project_number:
            # Use project number if provided
            projects = self.list_all_projects()
            if 1 <= self.args.project_number <= len(projects):
                _, munged_name, project_dir, _, _ = projects[self.args.project_number - 1]
                return (munged_name, project_dir)
            else:
                raise ValueError(f"Invalid project number: {self.args.project_number}. Must be between 1 and {len(projects)}")
        
        # Show progress while calculating
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            # Check if cache exists
            cache_file = Path(self.args.out_dir) / PROJECTS_CACHE_FILE
            if cache_file.exists():
                task = progress.add_task("Loading projects (using cache for unchanged projects)...", total=None)
            else:
                task = progress.add_task("Calculating project sizes and estimating token count...", total=None)
            
            projects = self.list_all_projects()
            progress.stop()
        
        if not projects:
            self.console.print("[red]No Claude projects found in ~/.claude/projects/[/red]")
            sys.exit(1)
        
        # Create rich table with more readable colors
        mode_display = "Rules Analysis (Performance Improvement)" if self.args.mode == "rules" else "Knowledge Extraction"
        table = Table(title=f"Available Claude Projects - {mode_display} Mode", show_lines=True)
        table.add_column("#", style="bright_cyan", justify="right")
        table.add_column("Project Name", style="bright_green")
        table.add_column("Size", style="bright_blue", justify="right")
        table.add_column("Tokens", style="bright_yellow", justify="right")
        if show_costs:
            table.add_column("Est. Cost", style="bright_magenta", justify="right")
        
        # Add rows
        for i, (friendly_name, munged_name, _, size_bytes, token_count) in enumerate(projects, 1):
            size_str = self.format_file_size(size_bytes)
            token_str = self.format_token_count(token_count)
            
            if show_costs:
                cost = self.estimate_cost(token_count)
                cost_str = f"${cost:.2f}"
                table.add_row(
                    str(i),
                    friendly_name,
                    size_str,
                    token_str,
                    cost_str
                )
            else:
                table.add_row(
                    str(i),
                    friendly_name,
                    size_str,
                    token_str
                )
        
        self.console.print("\n")
        self.console.print(table)
        if show_costs:
            self.console.print(f"\n[dim]Pricing: ${PRICE_PER_M_INPUT:.2f}/M input tokens, ${PRICE_PER_M_OUTPUT:.2f}/M output tokens (max {MAX_OUTPUT_TOKENS:,} output)[/dim]")
        else:
            self.console.print("\n[dim]Using Gemini CLI with -p flag for free analysis[/dim]")
        
        # Add note about analysis mode
        if self.args.mode == "rules":
            self.console.print("\n[yellow]Note: Using Rules mode by default. This will analyze conversations to identify[/yellow]")
            self.console.print("[yellow]assistant failures and generate corrective rules. Use --mode knowledge for[/yellow]")
            self.console.print("[yellow]traditional project analysis (decisions, mistakes, milestones).[/yellow]")
        
        while True:
            try:
                if self.args.yes:
                    self.console.print("[red]Cannot use --yes without --project-number[/red]")
                    sys.exit(1)
                
                choice = self.console.input("\n[bold]Select a project number (or 'q' to quit):[/bold] ")
                if choice.lower() == 'q':
                    sys.exit(0)
                
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    _, munged_name, project_dir, _, _ = projects[idx]
                    return (munged_name, project_dir)
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(projects)}[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")
    
    def run(self):
        """Main execution method."""
        print(f"[DEBUG] Starting run, GOOGLE_APPLICATION_CREDENTIALS={'set' if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else 'not set'}")
        
        # Choose analysis method before showing project list
        analysis_method = self.choose_analysis_method()
        use_cli = (analysis_method == "cli")
        print(f"[DEBUG] Analysis method: {analysis_method}")
        
        if not self.args.project:
            # No argument provided - show interactive selection
            munged_path, project_dir = self.select_project_interactive(show_costs=not use_cli)
            project_path = self.get_full_path_from_munged(munged_path)
        else:
            # Argument provided - could be path or friendly name
            arg = self.args.project
            
            # Try to find by friendly name or path
            result = self.find_project_by_name(arg)
            if result:
                munged_path, project_dir = result
                project_path = self.get_full_path_from_munged(munged_path) if "/" not in arg else arg
            else:
                # Fallback to treating it as a path
                project_path = arg
                munged_path = self.munge_project_path(project_path)
                project_dir = CLAUDE_PROJECTS_DIR / munged_path
                
                if not project_dir.exists():
                    print(f"Error: Project not found: {arg}")
                    print("\nTry running without arguments to see available projects.")
                    sys.exit(1)
        
        # Check for ambiguity
        ambiguities = self.check_ambiguous_paths(munged_path)
        if ambiguities:
            print("WARNING: Path might be ambiguous!")
            print("The following project paths would map to the same folder:")
            for amb in ambiguities:
                print(f"  - {amb}")
            print("\nPlease rename your projects to avoid ambiguity.")
            if not self.args.yes:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    sys.exit(1)
            else:
                print("Continuing due to --yes flag...")
        
        # Display analysis mode
        mode_display = "Rules Analysis (Performance Improvement)" if self.args.mode == "rules" else "Knowledge Extraction"
        print(f"\n[Analysis Mode: {mode_display}]")
        
        print(f"\nProject: {self.get_human_friendly_name(munged_path)}")
        print(f"Full path: {project_path}")
        print(f"Looking for files in: {project_dir}")
        
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(self.args.out_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Check for existing report and last run date
            if self.args.output:
                output_file = self.args.output
                # If output filename is not absolute, place it in the output directory
                if not Path(output_file).is_absolute():
                    output_file = output_dir / output_file
            else:
                prefix = self.get_output_prefix()
                output_file = output_dir / f"{prefix}_{self.get_human_friendly_name(munged_path).replace(' ', '_').lower()}.md"
            output_path = Path(output_file)
            last_run_date = self.get_last_run_date(output_path)
            is_differential = last_run_date is not None
            
            # Read JSONL files (differential or full)
            content = self.read_jsonl_files(project_dir, since_date=last_run_date)
            
            if is_differential and not content:
                print("\nNo new conversations since last run. Report is up to date.")
                return
            
            print(f"\nTotal content size: {len(content)} characters")
            
            # Check if we need to handle Google credentials
            # This affects both CLI and API usage since expired credentials can interfere with either
            self.check_google_credentials()
            
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
                    chunks = self.chunk_content(content)
                    print(f"New content split into {len(chunks)} chunks for analysis.")
                    subreports = []
                    with tqdm(total=len(chunks), desc="Analyzing new chunks", unit="chunk") as pbar:
                        for i, chunk in enumerate(chunks, 1):
                            chunk_size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
                            pbar.set_description(f"Analyzing chunk {i}/{len(chunks)} ({chunk_size_mb:.2f}MB)")
                            
                            subreport = self.analyze_chunk_with_gemini(chunk, i, len(chunks), use_cli)
                            subreports.append(subreport)
                            pbar.update(1)
                    
                    # Consolidate new content reports
                    new_analysis = self.consolidate_reports(subreports, use_cli)
                else:
                    # Single chunk for new content
                    print("Analyzing new conversations...")
                    new_analysis = self.analyze_chunk_with_gemini(content, 1, 1, use_cli)
                
                # Consolidate with existing report
                print("\nMerging with existing report...")
                
                if use_cli:
                    # Use CLI for differential consolidation
                    combined_content = f"PREVIOUS REPORT:\n\n{existing_report}\n\n---NEW CONVERSATIONS ANALYSIS---\n\n{new_analysis}"
                    prompt = self.get_differential_consolidation_prompt()
                    
                    for attempt in range(MAX_RETRIES):
                        try:
                            # Prepare the full prompt content
                            full_prompt = f"{prompt}\n\n{combined_content}"
                            
                            # Build command with flash model to avoid Pro quota issues
                            cmd = ["gemini", "-m", "gemini-2.5-flash"]

                            # Use the logging wrapper - pass content directly via stdin
                            result = self.run_gemini_cli_with_logging(cmd, full_prompt, attempt)
                            
                            analysis = result.stdout
                            break # Exit retry loop on success
                        except subprocess.TimeoutExpired as e:
                            # Check if it's actually a rate limit disguised as a timeout
                            stderr_text = ""
                            if hasattr(e, 'stderr') and e.stderr:
                                stderr_text = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                                
                            is_rate_limit = "429" in stderr_text or "RESOURCE_EXHAUSTED" in stderr_text or "Quota exceeded" in stderr_text
                            
                            if is_rate_limit:
                                print(f"\n[yellow]Gemini CLI hit rate limit (detected in timeout).[/yellow]")
                                if "Gemini 2.5 Pro" in stderr_text and not self._gemini_model_override_active:
                                    self._gemini_model_override_active = True
                                    print(f"[yellow]Switching from Pro to Flash model due to quota limits.[/yellow]")
                            else:
                                print(f"\n[yellow]Gemini CLI timed out after {GEMINI_CLI_TIMEOUT} seconds.[/yellow]")
                            
                            # Show the command that timed out
                            print(f"[dim]Command: {' '.join(cmd)}[/dim]")
                            print(f"[dim]Attempt {attempt + 1}/{MAX_RETRIES}[/dim]")
                            
                            # Show partial stderr if available
                            if stderr_text:
                                # Extract the most relevant error message
                                if "message" in stderr_text:
                                    try:
                                        import re
                                        match = re.search(r'"message":\s*"([^"]+)"', stderr_text)
                                        if match:
                                            print(f"[red]Error: {match.group(1)}[/red]")
                                    except:
                                        pass
                                else:
                                    print(f"[dim]Partial error: {stderr_text[:300]}...[/dim]")
                            
                            wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                            print(f"\nRetrying in {wait_time:.1f} seconds...")
                            time.sleep(wait_time)
                        except subprocess.CalledProcessError as e:
                            if "429" in e.stderr or "RESOURCE_EXHAUSTED" in e.stderr:
                                if not self._gemini_model_override_active:
                                    self._gemini_model_override_active = True
                                    print("\n[yellow]Rate limit hit. Switching to 'gemini-2.5-flash' model for subsequent calls.[/yellow]")
                                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                                print(f"\nGemini CLI rate limit hit (429). Retrying in {wait_time:.1f} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                                time.sleep(wait_time)
                            else:
                                raise RuntimeError(f"Gemini CLI failed: {e.stderr}")
                    else:
                        raise RuntimeError(f"Gemini CLI failed after {MAX_RETRIES} attempts due to rate limiting.")
                else:
                    # Use API for differential consolidation
                    client = self.get_gemini_client()
                    prompt = self.get_differential_consolidation_prompt()
                    
                    combined_content = f"PREVIOUS REPORT:\n\n{existing_report}\n\n---NEW CONVERSATIONS ANALYSIS---\n\n{new_analysis}"
                    
                    response = client.chat.completions.create(
                        model=GEMINI_MODEL,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": combined_content}
                        ],
                        temperature=0.0
                    )
                    time.sleep(1) # Rate limit to 60 requests/minute
                    analysis = response.choices[0].message.content or ""
                
            else:
                # Full analysis mode (same as before)
                chunks = self.chunk_content(content)
                num_chunks = len(chunks)
                
                if num_chunks == 1:
                    print("Content fits in a single chunk, analyzing directly...")
                    analysis = self.analyze_chunk_with_gemini(chunks[0], 1, 1, use_cli)
                    subreports = [analysis]
                else:
                    print(f"\nContent split into {num_chunks} chunks for analysis.")
                    print(f"Note: This may take several minutes for large projects.\n")
                    
                    subreports = []
                    subreport_files = []  # Track files for cleanup
                    with tqdm(total=num_chunks, desc="Analyzing chunks", unit="chunk") as pbar:
                        for i, chunk in enumerate(chunks, 1):
                            chunk_size_mb = len(chunk.encode('utf-8')) / (1024 * 1024)
                            pbar.set_description(f"Analyzing chunk {i}/{num_chunks} ({chunk_size_mb:.2f}MB)")
                            
                            subreport = self.analyze_chunk_with_gemini(chunk, i, num_chunks, use_cli)
                            
                            # Save subreport
                            if self.args.output:
                                # Use custom output base name for subreports
                                base_name = Path(self.args.output).stem
                                subreport_filename = f"subreport_{base_name}_chunk{i}.md"
                            else:
                                prefix = self.get_output_prefix()
                                subreport_filename = f"subreport_{prefix}_{self.get_human_friendly_name(munged_path).replace(' ', '_').lower()}_chunk{i}.md"
                            subreport_file = output_dir / subreport_filename
                            subreport_files.append(subreport_file)  # Track for cleanup
                            
                            with open(subreport_file, 'w') as f:
                                f.write(f"# Subreport {i}/{num_chunks}: {self.get_human_friendly_name(munged_path)}\n\n")
                                f.write(subreport)
                            
                            subreports.append(subreport)
                            pbar.update(1)
                    
                    # Consolidate reports
                    analysis = self.consolidate_reports(subreports, use_cli)
            
            # Format the final report
            final_report = self.format_final_report(
                analysis,
                self.get_human_friendly_name(munged_path),
                project_path,
                is_differential=is_differential,
                current_run_time=current_run_time,
                last_run_date=last_run_date,
                num_chunks=num_chunks if not is_differential else 1
            )
            
            # Save the final analysis with metadata
            with open(output_file, 'w') as f:
                f.write(final_report)
                f.write(f"\n\n{METADATA_MARKER} {current_run_time.isoformat()} -->")
            
            if is_differential:
                print(f"\nDifferential update completed. Report saved to: {output_file}")
            else:
                print(f"\nFull analysis completed. Report saved to: {output_file}")
                
                # Clean up subreport files unless --keep-subchunk-reports is specified
                if 'subreport_files' in locals() and subreport_files and not self.args.keep_subchunk_reports:
                    print(f"\nCleaning up {len(subreport_files)} subreport files...")
                    for subreport_file in subreport_files:
                        try:
                            subreport_file.unlink()
                        except Exception as e:
                            print(f"Warning: Could not delete {subreport_file}: {e}")
                    print("Subreport cleanup completed.")
                elif 'subreport_files' in locals() and subreport_files and self.args.keep_subchunk_reports:
                    print(f"\nKept {len(subreport_files)} subreport files in {output_dir}/")
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


class KnowledgeAnalyzer(ConversationAnalyzer):
    """Analyzer for extracting decisions, mistakes, and milestones."""
    
    def get_analysis_prompt(self) -> str:
        return """Analyze this Claude conversation history and identify:

1. **Significant Decisions**: Key choices made during the project development
2. **Mistakes**: Errors, incorrect approaches, or issues that needed fixing
3. **Milestones**: Important achievements or completed features
4. **Timeline**: A chronological overview of the project's progression

Format the output as a Markdown document with clear sections for each category. 
Include specific examples and quotes where relevant. Include important dates and times.
Be concise but thorough."""
    
    def get_consolidation_prompt(self) -> str:
        return """Consolidate these subreports into one single final report. 
Merge all decisions, mistakes, milestones, and timeline entries from all subreports.
Remove any duplicates and organize chronologically where appropriate.
Maintain the same section structure: Significant Decisions, Mistakes, Milestones, and Timeline."""
    
    def get_differential_consolidation_prompt(self) -> str:
        return """Consolidate this previous report with this new report, preserving timelines.
The first part is the previous full report. The second part contains new conversations since the last run.
Merge all content appropriately:
- Add new decisions, mistakes, and milestones to existing sections
- Extend the timeline with new events
- Remove any duplicates
- Maintain chronological order where appropriate
Keep the same section structure: Significant Decisions, Mistakes, Milestones, and Timeline."""
    
    def get_output_prefix(self) -> str:
        return "knowledge"
    
    def format_final_report(self, content: str, project_name: str, 
                          project_path: str, **kwargs) -> str:
        report = f"# Claude Project Analysis: {project_name}\n\n"
        report += f"**Full Path**: {project_path}\n\n"
        if kwargs.get('is_differential'):
            report += f"**Last Updated**: {kwargs['current_run_time'].isoformat()}\n\n"
            report += f"**Update Type**: Differential (changes since {kwargs['last_run_date'].isoformat()})\n\n"
        elif kwargs.get('num_chunks', 1) > 1:
            report += f"**Note**: This analysis was generated from {kwargs['num_chunks']} chunks. "
            report += "See subreport files for detailed chunk analyses.\n\n"
        report += content
        return report


class RulesAnalyzer(ConversationAnalyzer):
    """Analyzer for extracting behavioral rules and improvement suggestions."""
    
    def __init__(self, args):
        super().__init__(args)
        self._ensure_hooks_documentation()
    
    def _ensure_hooks_documentation(self):
        """Create Claude hooks documentation if it doesn't exist."""
        docs_dir = Path("docs/research")
        docs_dir.mkdir(parents=True, exist_ok=True)
        hooks_file = docs_dir / "claude-hooks.md"
        
        if not hooks_file.exists():
            hooks_content = """# Claude Hooks Documentation

## Overview
Claude hooks are user-defined shell commands that execute at specific points in Claude Code's lifecycle.

## Event Types
- **PreToolUse**: Runs before tool calls (can block/modify)
- **PostToolUse**: Runs after tool completion
- **Notification**: Custom notifications
- **Stop**: When Claude finishes responding
- **SubagentStop**: When subagents finish

## Matcher Patterns
- `tool_name`: Match specific tools (e.g., "Write", "Edit")
- `file_paths`: Match file patterns (e.g., ["*.py", "api/**/*.ts"])
- Empty matcher: Matches all events of that type

## Environment Variables
- `$CLAUDE_FILE_PATHS`: Space-separated file paths
- `$CLAUDE_TOOL_OUTPUT`: Output from tool execution
- `$CLAUDE_NOTIFICATION`: Notification content

## Example Hook Configuration
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": {
          "tool_name": "Write"
        },
        "hooks": [
          {
            "type": "command",
            "command": "echo 'About to write file: $CLAUDE_FILE_PATHS'"
          }
        ]
      }
    ]
  }
}
```

## Best Practices
- Always quote shell variables: "$VAR" not $VAR
- Use absolute paths for scripts
- Validate inputs before processing
- Return appropriate exit codes to control flow
- Test hooks thoroughly before deployment"""
            hooks_file.write_text(hooks_content)
            print(f"Created hooks documentation at: {hooks_file}")
    
    def get_analysis_prompt(self) -> str:
        return """You are an expert corporate performance psychologist. You have deep insight into the human psyche. Your job is to analyse the provided conversations between the AI assistant and the User to produce a list of up to 100 incidents in the conversation where the assistant upset, angered, frustrated, or confused the user due to not meeting expectations, being unprofessional, lazy, ambiguous, whimsical, lacking tenacity, incompetent, or stupid. The goal is collating a list of corrective and preventative rules for the assistant to avoid having them happen again. 

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
    
    def get_consolidation_prompt(self) -> str:
        return """Consolidate these rule analysis subreports into one final report.
Merge all incidents and rules from all subreports.
Remove duplicates and organize by severity/frequency.
Maintain the two-section structure: 
1. CLAUDE.md Candidates (text rules)
2. Claude Hooks Candidates (formatted as a table with: Proposed Hook | Example It Prevents | Event Type | Matcher Pattern | Command)"""
    
    def get_differential_consolidation_prompt(self) -> str:
        return """Consolidate this previous rules report with new incidents.
The first part is the previous report. The second part contains new conversations.
Merge appropriately:
- Add new incidents and rules
- Update frequency counts for repeated patterns
- Maintain the two-section structure
- Keep the hooks table format intact
- Keep rules organized by severity/impact"""
    
    def get_output_prefix(self) -> str:
        return "rules"
    
    def format_final_report(self, content: str, project_name: str, 
                          project_path: str, **kwargs) -> str:
        report = f"# Claude Assistant Performance Rules: {project_name}\n\n"
        report += f"**Project Path**: {project_path}\n\n"
        report += f"**Analysis Date**: {datetime.now().strftime('%d-%m-%Y')}\n\n"
        if kwargs.get('is_differential'):
            report += f"**Update Type**: Differential (new incidents since {kwargs['last_run_date'].isoformat()})\n\n"
        report += "**Purpose**: Identify patterns where the assistant failed to meet expectations "
        report += "and provide corrective rules.\n\n"
        report += content
        return report


def create_analyzer(mode: str, args: argparse.Namespace) -> ConversationAnalyzer:
    """Factory function to create the appropriate analyzer."""
    if mode == "knowledge":
        return KnowledgeAnalyzer(args)
    elif mode == "rules":
        return RulesAnalyzer(args)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Claude conversation history")
    parser.add_argument("project", nargs="?", help="Project name or path")
    parser.add_argument("--mode", choices=["rules", "knowledge"], default="rules",
                        help="Analysis mode: rules (default) or knowledge")
    parser.add_argument("--output", "-o", help="Output file name")
    parser.add_argument("--out-dir", default="reports", help="Output directory")
    parser.add_argument("--force-gemini-cli", action="store_true",
                        help="Force use of Gemini CLI")
    parser.add_argument("--force-api", action="store_true",
                        help="Force use of API")
    parser.add_argument("--project-number", type=int,
                        help="Select project by number (1-based)")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Auto-confirm all prompts")
    parser.add_argument("--keep-subchunk-reports", action="store_true",
                        help="Keep intermediate subchunk report files")
    
    args = parser.parse_args()
    
    # Create the appropriate analyzer
    analyzer = create_analyzer(args.mode, args)
    
    # Run the analysis
    analyzer.run()


if __name__ == "__main__":
    main()