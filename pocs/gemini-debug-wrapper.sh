#!/bin/bash
# Debug wrapper for gemini CLI to see what's actually happening

echo "[WRAPPER] ========== GEMINI DEBUG WRAPPER ==========" >&2
echo "[WRAPPER] Date: $(date)" >&2
echo "[WRAPPER] PID: $$" >&2
echo "[WRAPPER] Command: gemini $@" >&2
echo "[WRAPPER] Working dir: $(pwd)" >&2
echo "[WRAPPER] Environment variables:" >&2
echo "[WRAPPER]   PATH: $PATH" >&2
echo "[WRAPPER]   GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS:-NOT SET}" >&2
echo "[WRAPPER]   HOME: $HOME" >&2
echo "[WRAPPER]   USER: $USER" >&2

# Check what gemini auth files exist
echo "[WRAPPER] Auth files check:" >&2
if [ -f "$HOME/.gemini/oauth_creds.json" ]; then
    echo "[WRAPPER]   ~/.gemini/oauth_creds.json exists ($(stat -f%z "$HOME/.gemini/oauth_creds.json" 2>/dev/null || stat -c%s "$HOME/.gemini/oauth_creds.json" 2>/dev/null) bytes)" >&2
else
    echo "[WRAPPER]   ~/.gemini/oauth_creds.json NOT FOUND" >&2
fi

# Check if stdin has data
if [ -t 0 ]; then
    echo "[WRAPPER] No stdin data (terminal mode)" >&2
else
    echo "[WRAPPER] Stdin data detected (piped mode)" >&2
fi

echo "[WRAPPER] Starting actual gemini command..." >&2
echo "[WRAPPER] =======================================" >&2

# Use exec to replace this process with gemini
exec /Users/julian/.nvm/versions/node/v22.15.0/bin/gemini "$@"