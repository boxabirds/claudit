# Claude Conversation Analyzer

A powerful tool that analyzes Claude conversation history with two modes:
- **Knowledge Mode**: Extract significant decisions, mistakes, milestones, and timeline from your projects
- **Rules Mode** (default): Identify assistant behavior issues and generate corrective rules for improvement

## 🎉 FREE ANALYSIS OPTION AVAILABLE! 🎉

**Use Gemini CLI with the `-p` flag for free or significantly reduced cost analysis!**

If you have Gemini CLI installed, this tool will automatically offer to use it for free analysis. Login with Google to access a generous free tier.

## ⚠️ COST WARNING (When Using API) ⚠️

**THIS TOOL CAN BE VERY EXPENSIVE WHEN USING THE API!**

- Analyzing a single large project can cost **$5-10 or more**
- The "Awesome Agent Showcase" project (58.5MB) costs approximately **$6.93** to analyze
- Costs are based on Google Gemini 2.5 Flash pricing ($0.30/M input tokens, $2.50/M output tokens)
- Always check the estimated cost in the project listing before proceeding (not shown when using CLI)

## Features

- **Two Analysis Modes**:
  - **Rules Mode** (default): Analyzes conversations to identify assistant failures and generate corrective rules
  - **Knowledge Mode**: Extracts decisions, mistakes, milestones, and timeline
- **FREE Analysis Option**: Automatic detection and use of Gemini CLI for free/reduced cost analysis
- **Full Automation Support**: New command-line options for scripting and CI/CD integration
- **Interactive Project Selection**: Browse all your Claude projects with size and token estimates
- **Differential Updates**: Only analyzes new conversations since the last run
- **Smart Chunking**: Handles large projects by splitting into manageable chunks
- **Image Stripping**: Removes base64-encoded images to reduce payload size
- **Beautiful Terminal UI**: Uses Rich library for formatted tables and progress bars
- **Token Counting**: Accurate token estimates using tiktoken
- **Claude Hooks Support**: Rules mode suggests hooks for automating rule enforcement

## Installation

1. Ensure you have Python 3.12 or later installed
2. Clone this repository
3. Navigate to the `claudit-analyzer` directory
4. Install dependencies using uv:

```bash
cd claudit-analyzer
uv venv -p 3.12
uv add openai tiktoken rich tqdm
```

5. (Optional) Install Gemini CLI for free analysis:

```bash
pip install google-generativeai
```

## Setup

### Option 1: Use Gemini CLI (Recommended - FREE!)

1. Install Gemini CLI: `pip install google-generativeai`
2. Run the tool - it will automatically detect and offer to use Gemini CLI
3. Login with Google when prompted to access the free tier

### Option 2: Use API Key

1. Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Export your API key:

```bash
export GEMINI_API_KEY=your_api_key_here
```

## Usage

### Interactive Mode (Recommended)

Run without arguments to see all projects and select one:

```bash
./claudit
```

This will:
1. Check for Gemini CLI and offer free analysis option
2. Display a table showing project names, sizes, and token counts
3. Show cost estimates (only when using API, not CLI)
4. Use Rules mode by default (identify assistant issues)

### Direct Analysis

Analyze a specific project by name:

```bash
./claudit "Project Name"
```

Or by full path:

```bash
./claudit /Users/username/projects/myproject
```

### Analysis Modes

Choose between two analysis modes:

```bash
# Rules mode (default) - Generate corrective rules for assistant improvement
./claudit --mode rules "Project Name"

# Knowledge mode - Extract decisions, mistakes, and milestones
./claudit --mode knowledge "Project Name"
```

### Automation Options

New command-line options for full automation:

```bash
# Select project by number from list
./claudit --project-number 3

# Force specific analysis method
./claudit --force-gemini-cli  # Use Gemini CLI
./claudit --force-api         # Use API key

# Auto-confirm all prompts
./claudit --yes

# Ignore Google credentials warnings
./claudit --ignore-google-creds

# Combine options for full automation
./claudit --mode rules --force-gemini-cli --project-number 1 --yes --ignore-google-creds

# Batch process multiple projects
for i in {1..5}; do
    ./claudit --project-number $i --force-gemini-cli --yes
done
```

## How It Works

1. **Detects Analysis Method**: Checks for Gemini CLI and API key availability
2. **Reads JSONL Files**: Scans `~/.claude/projects/` for conversation history
3. **Filters Content**: Keeps only essential fields (message, timestamp, children, type)
4. **Strips Images**: Replaces base64-encoded images with placeholders
5. **Chunks Large Content**: Splits conversations larger than 1MB into chunks
6. **Analyzes with Gemini**: Uses either CLI or API for analysis
7. **Generates Report**: Creates markdown report based on mode:
   
   **Knowledge Mode**:
   - Significant Decisions
   - Mistakes and Errors
   - Project Milestones
   - Timeline of Events
   
   **Rules Mode**:
   - CLAUDE.md Candidates: Concise rules for system prompts
   - Claude Hooks Candidates: Automated rules with hook configurations

## Differential Updates

After the first analysis, subsequent runs only process new conversations:
- Detects existing reports and extracts last run timestamp
- Only processes files created or modified since last run
- Merges new analysis with existing report
- Significantly reduces cost for regular updates

## Output

Reports are saved in the `reports/` directory with mode-specific prefixes:
- **Knowledge Mode**: `knowledge_<project_name>.md`
- **Rules Mode**: `rules_<project_name>.md`

For large projects split into chunks, individual subreports are also saved.

In Rules mode, a `docs/research/claude-hooks.md` file is created with comprehensive hooks documentation.

## Cost Breakdown (API Only)

When using the API, the tool estimates worst-case costs assuming maximum output (65,535 tokens):

| Project Size | Tokens | Estimated Cost |
|-------------|--------|----------------|
| < 100KB | < 50k | ~$0.17 |
| 1MB | ~300k | ~$0.25 |
| 10MB | ~3M | ~$1.00 |
| 50MB | ~15M | ~$4.50 |

**Note**: When using Gemini CLI with `-p` flag, analysis is FREE with Google login!

## Performance Tips

1. **Use Gemini CLI**: The free tier is generous and suitable for most projects
2. **Start Small**: Test with smaller projects first
3. **Use Differential Updates**: Run regularly to analyze only new content
4. **Check Token Counts**: Review the token count before proceeding
5. **Monitor Usage**: Keep track of your API usage if not using CLI

## Technical Details

- Uses OpenAI-compatible API endpoint for Gemini when using API
- Runs Gemini CLI with `-p` flag for free tier access
- Implements retry logic and error handling
- Preserves conversation structure while filtering noise
- Handles malformed JSON gracefully
- Supports projects with multiple conversation files
- Gemini CLI calls have a 15-second timeout to prevent hanging on authentication prompts

## Limitations

- Cannot perfectly distinguish folder boundaries in munged paths
- Image stripping only removes base64-encoded images
- Cost estimates assume maximum output tokens
- Requires good internet connection for API calls
- Gemini CLI may have different rate limits than API
- Gemini CLI calls timeout after 15 seconds (configurable via GEMINI_CLI_TIMEOUT constant)

## License

This tool is provided as-is. Use at your own risk and expense.