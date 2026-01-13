#!/bin/bash

# Test script for multiple YouTube video URLs
VIDEOS=(
    "vdZAN4NbEoU"
    "WcUoqVjMLWM"
    "bP_vzHICa4I"
    "RRS0RcEccQM"
    "qByLpjxeNv8"
    "KIY8LvL4Kog"
)

BASE_URL="http://localhost:5485/transcript"

echo "============================================================"
echo "Testing YouTube Transcript Service"
echo "============================================================"
echo ""

for video_id in "${VIDEOS[@]}"; do
    echo "--- Testing: $video_id ---"
    echo "URL: https://www.youtube.com/watch?v=$video_id"
    
    start_time=$(date +%s.%N)
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" "$BASE_URL/$video_id?force=1")
    end_time=$(date +%s.%N)
    
    # Extract HTTP code and time
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME_TOTAL:" | cut -d: -f2)
    json_response=$(echo "$response" | grep -v "HTTP_CODE:" | grep -v "TIME_TOTAL:")
    
    elapsed=$(echo "$end_time - $start_time" | bc)
    
    echo "HTTP Status: $http_code"
    echo "Curl Time: ${time_total}s"
    echo "Total Elapsed: ${elapsed}s"
    
    # Check if we got an error
    if echo "$json_response" | grep -q '"error"'; then
        error_msg=$(echo "$json_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'Unknown error'))" 2>/dev/null || echo "Error parsing")
        echo "❌ ERROR: $error_msg"
    elif echo "$json_response" | grep -q '"transcript"'; then
        transcript_count=$(echo "$json_response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('transcript', [])))" 2>/dev/null || echo "?")
        cached=$(echo "$json_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('cached', '?'))" 2>/dev/null || echo "?")
        echo "✅ SUCCESS: Found $transcript_count transcript segments (cached: $cached)"
    else
        echo "⚠️  UNKNOWN RESPONSE"
        echo "$json_response" | head -5
    fi
    
    echo ""
done

echo "============================================================"
echo "Testing Complete"
echo "============================================================"
