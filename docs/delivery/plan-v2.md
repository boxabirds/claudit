# Revised Plan: Add Rules Analysis Feature with Class-Based Architecture

## Overview
Refactor the tool to use an object-oriented architecture with an abstract base class that handles all common logic, and two concrete implementations for Knowledge and Rules analysis.

## Architecture Design

### 1. Class Hierarchy
```python
from abc import ABC, abstractmethod

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
    
    # All existing methods become class methods:
    def check_google_credentials(self):
        """Check if GOOGLE_APPLICATION_CREDENTIALS is set."""
        # Existing logic, using self.args.ignore_google_creds
    
    def choose_analysis_method(self):
        """Choose between CLI and API."""
        if self.args.force_gemini_cli:
            return "cli"
        if self.args.force_api:
            return "api"
        # ... existing interactive logic
    
    def analyze_chunk_with_gemini(self, content: str, chunk_num: int, 
                                 total_chunks: int, use_cli: bool = False):
        """Analyze a chunk using the appropriate prompt."""
        prompt = self.get_analysis_prompt()
        # ... rest of existing logic
    
    def consolidate_reports(self, subreports: List[str], use_cli: bool = False):
        """Consolidate using the appropriate prompt."""
        prompt = self.get_consolidation_prompt()
        # ... rest of existing logic
    
    def run(self):
        """Main execution method."""
        # All the main() logic goes here

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
- Test hooks thoroughly before deployment
"""
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
```

### 2. Factory Function
```python
def create_analyzer(mode: str, args: argparse.Namespace) -> ConversationAnalyzer:
    """Factory function to create the appropriate analyzer."""
    if mode == "knowledge":
        return KnowledgeAnalyzer(args)
    elif mode == "rules":
        return RulesAnalyzer(args)
    else:
        raise ValueError(f"Unknown mode: {mode}")
```

### 3. Updated Main Function
```python
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
    parser.add_argument("--ignore-google-creds", action="store_true",
                        help="Automatically ignore GOOGLE_APPLICATION_CREDENTIALS")
    parser.add_argument("--keep-subchunk-reports", action="store_true",
                        help="Keep intermediate subchunk report files")
    
    args = parser.parse_args()
    
    # Create the appropriate analyzer
    analyzer = create_analyzer(args.mode, args)
    
    # Run the analysis
    analyzer.run()
```

### 4. Benefits of Class-Based Architecture

1. **Clean Separation**: Analysis logic is clearly separated from mode-specific prompts
2. **Easy Extension**: Adding new analysis modes is trivial - just create a new subclass
3. **Code Reuse**: All common functionality lives in the base class
4. **Type Safety**: Abstract methods ensure all analyzers implement required functionality
5. **Testability**: Each analyzer can be tested independently
6. **Maintainability**: Changes to core logic happen in one place

### 5. Migration Strategy

1. Create the class hierarchy alongside existing code
2. Move functions into the base class as methods
3. Replace global variables with instance variables
4. Update main() to use the factory pattern
5. Test both modes thoroughly
6. Remove old procedural code

### 6. Command-Line Options Summary

New options added for full automation:
- `--mode [rules|knowledge]` - Choose analysis type (default: rules)
- `--force-gemini-cli` - Skip API check, use CLI
- `--force-api` - Skip CLI check, use API
- `--project-number <n>` - Select project by number from list
- `--yes` - Auto-confirm all prompts
- `--ignore-google-creds` - Auto-ignore GOOGLE_APPLICATION_CREDENTIALS

### 7. Testing Commands

```bash
# Test rules mode with CLI, project 3, auto-confirm
./claudit --mode rules --force-gemini-cli --project-number 3 --yes

# Test knowledge mode with API, ignore Google creds
./claudit --mode knowledge --force-api --ignore-google-creds --project-number 1

# Test default (rules) with specific project
./claudit "dspy-kg" --yes

# Batch process multiple projects
for i in {1..5}; do
    ./claudit --project-number $i --force-gemini-cli --yes
done
```

This architecture provides a clean, extensible foundation for the tool while maintaining all existing functionality.