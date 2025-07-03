# Claude Conversation Analyzer

A tool that analyzes Claude conversation history to extract significant decisions, mistakes, milestones, and timeline from your projects.

##   COST WARNING  

**THIS TOOL CAN BE VERY EXPENSIVE TO RUN!**

- Analyzing a single large project can cost **$5-10 or more**
- The "Awesome Agent Showcase" project (58.5MB) costs approximately **$6.93** to analyze
- Costs are based on Google Gemini 2.5 Flash pricing ($0.30/M input tokens, $2.50/M output tokens)
- Always check the estimated cost in the project listing before proceeding

## Features

- **Interactive Project Selection**: Browse all your Claude projects with size and cost estimates
- **Differential Updates**: Only analyzes new conversations since the last run
- **Smart Chunking**: Handles large projects by splitting into manageable chunks
- **Image Stripping**: Removes base64-encoded images to reduce payload size
- **Beautiful Terminal UI**: Uses Rich library for formatted tables and progress bars
- **Token Counting**: Accurate token estimates using tiktoken
- **Timeline Analysis**: Generates chronological overview of project development

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

## Setup

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

This will display a table showing:
- Project names
- File sizes (KB/MB)
- Token counts
- **Estimated analysis cost**

### Direct Analysis

Analyze a specific project by name:

```bash
./claudit "Project Name"
```

Or by full path:

```bash
./claudit /Users/username/projects/myproject
```

## How It Works

1. **Reads JSONL Files**: Scans `~/.claude/projects/` for conversation history
2. **Filters Content**: Keeps only essential fields (message, timestamp, children, type)
3. **Strips Images**: Replaces base64-encoded images with placeholders
4. **Chunks Large Content**: Splits conversations larger than 1MB into chunks
5. **Analyzes with Gemini**: Sends to Gemini 2.5 Flash for analysis
6. **Generates Report**: Creates markdown report with:
   - Significant Decisions
   - Mistakes and Errors
   - Project Milestones
   - Timeline of Events

## Differential Updates

After the first analysis, subsequent runs only process new conversations:
- Detects existing reports and extracts last run timestamp
- Only processes files created or modified since last run
- Merges new analysis with existing report
- Significantly reduces cost for regular updates

## Output

Reports are saved as `analysis_<project_name>.md` in the current directory.

For large projects split into chunks, individual subreports are also saved.

## Cost Breakdown

The tool estimates worst-case costs assuming maximum output (65,535 tokens):

| Project Size | Tokens | Estimated Cost |
|-------------|--------|----------------|
| < 100KB | < 50k | ~$0.17 |
| 1MB | ~300k | ~$0.25 |
| 10MB | ~3M | ~$1.00 |
| 50MB | ~15M | ~$4.50 |

## Performance Tips

1. **Start Small**: Test with smaller projects first
2. **Use Differential Updates**: Run regularly to analyze only new content
3. **Check Estimates**: Always review the cost estimate before proceeding
4. **Monitor Usage**: Keep track of your Gemini API usage

## Technical Details

- Uses OpenAI-compatible API endpoint for Gemini
- Implements retry logic and error handling
- Preserves conversation structure while filtering noise
- Handles malformed JSON gracefully
- Supports projects with multiple conversation files

## Limitations

- Cannot perfectly distinguish folder boundaries in munged paths
- Image stripping only removes base64-encoded images
- Cost estimates assume maximum output tokens
- Requires good internet connection for API calls

## License

This tool is provided as-is. Use at your own risk and expense.