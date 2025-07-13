# Claude Hooks Documentation

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