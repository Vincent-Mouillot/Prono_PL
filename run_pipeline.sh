#!/bin/bash

# PROJECT_DIR is derived from the script's own location — works from dev or prod
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$PROJECT_DIR/table_output.txt"
LOG_FILE="$PROJECT_DIR/pipeline.log"

cd "$PROJECT_DIR" || exit 1

# NTFY_TOPIC (and the rest of the pipeline's secrets) lives in .env, not in this script
set -a
source .env
set +a
NTFY_URL="https://ntfy.sh/$NTFY_TOPIC"

# Step 1: Run the pipeline (full run log kept separately for debugging;
# pipeline.py writes just the predictions table, or "No match today", to $OUTPUT_FILE)
source .venv/bin/activate
python pipeline.py > "$LOG_FILE" 2>&1

# Step 2: Check if the output file exists and send the content via ntfy
if [[ -f "$OUTPUT_FILE" ]]; then
    table_output=$(cat "$OUTPUT_FILE")
    curl -d "$table_output" "$NTFY_URL"
    rm "$OUTPUT_FILE"
else
    echo "Error: output file does not exist."
fi
