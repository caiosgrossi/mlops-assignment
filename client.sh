#!/bin/bash

# Simple CLI client for Frontend API
# Usage: ./client.sh song1 song2 song3 ...

# Configuration
API_URL="${FRONTEND_API_URL:-http://frontend-api-service.caiogrossi.svc.cluster.local:5006/api/recommender}"
OUTPUT_FILE="response.out"

# Check if songs provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"song1\" \"song2\" \"song3\" ..."
    echo ""
    echo "Note: Use quotes to allow spaces in song names"
    echo ""
    echo "Example:"
    echo "  $0 \"song1\" \"song\""
    echo ""
    exit 1
fi

# Build JSON array of songs
SONGS_JSON="["
FIRST=true
for song in "$@"; do
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        SONGS_JSON+=","
    fi
    SONGS_JSON+="\"$song\""
done
SONGS_JSON+="]"

# Build complete JSON payload
JSON_PAYLOAD="{\"songs\": $SONGS_JSON}"

echo "==============================================="
echo "Frontend API CLI Client"
echo "==============================================="
echo "API Endpoint: $API_URL"
echo "Songs: $#"
echo "Payload: $JSON_PAYLOAD"
echo "==============================================="
echo ""

# Make request using wget
wget --server-response \
     --output-document "$OUTPUT_FILE" \
     --header='Content-Type: application/json' \
     --post-data "$JSON_PAYLOAD" \
     "$API_URL" 2>&1

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "==============================================="
    echo "Response received successfully!"
    echo "==============================================="
    echo ""
    cat "$OUTPUT_FILE" | python3 -m json.tool 2>/dev/null || cat "$OUTPUT_FILE"
    echo ""
else
    echo ""
    echo "==============================================="
    echo "Error: Request failed"
    echo "==============================================="
    exit 1
fi
