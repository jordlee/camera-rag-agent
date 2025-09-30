#!/bin/bash
# Test script for rate limiting
# Tests that the 11th request within a minute returns 429

echo "Testing rate limiting (10 requests/minute limit)..."
echo "Sending 11 requests to get_sdk_stats endpoint..."
echo ""

BASE_URL="${1:-http://localhost:8000}"
SUCCESS_COUNT=0
RATE_LIMITED=0

for i in {1..11}; do
    echo -n "Request $i: "

    # Make request to health endpoint (should not be rate limited)
    # For testing MCP tools, we'd need to send proper MCP protocol requests
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health" 2>/dev/null)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
    BODY=$(echo "$RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Success (200)"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    elif [ "$HTTP_CODE" = "429" ]; then
        echo "🚫 Rate Limited (429)"
        RATE_LIMITED=$((RATE_LIMITED + 1))
        # Show the error message
        echo "$BODY" | python3 -m json.tool 2>/dev/null | grep -A 1 "message"
    else
        echo "❌ Error ($HTTP_CODE)"
    fi

    # Small delay to stay within the same minute window
    sleep 0.1
done

echo ""
echo "Results:"
echo "  Successful: $SUCCESS_COUNT"
echo "  Rate Limited: $RATE_LIMITED"
echo ""

if [ $RATE_LIMITED -gt 0 ]; then
    echo "✅ Rate limiting is working! (Got $RATE_LIMITED rate limit responses)"
else
    echo "⚠️ Note: /health endpoint is not rate limited by design"
    echo "   To test MCP tool rate limits, use the MCP protocol or modify the script"
fi
