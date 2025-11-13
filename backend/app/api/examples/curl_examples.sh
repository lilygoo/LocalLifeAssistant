#!/bin/bash
# cURL Examples: Calling the Public Chat API
#
# This script demonstrates how to call the public chat API using cURL.
# You need a Firebase authentication token to use this API.
#
# Usage:
#   1. Set FIREBASE_TOKEN environment variable
#   2. Optionally set API_BASE_URL (default: http://localhost:8000)
#   3. Run: bash curl_examples.sh

# Configuration
FIREBASE_TOKEN="${FIREBASE_TOKEN:-YOUR_FIREBASE_TOKEN_HERE}"
# For production, set API_BASE_URL to your domain:
# export API_BASE_URL="https://your-domain.com"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_ENDPOINT="${API_BASE_URL}/api/public/chat"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Public Chat API - cURL Examples"
echo "============================================================"
echo ""

if [ "$FIREBASE_TOKEN" = "YOUR_FIREBASE_TOKEN_HERE" ]; then
    echo -e "${YELLOW}Warning: Please set FIREBASE_TOKEN environment variable${NC}"
    echo "Example: export FIREBASE_TOKEN='your-token-here'"
    echo ""
fi

echo "API Endpoint: ${API_ENDPOINT}"
echo "For production, set: export API_BASE_URL='https://your-domain.com'"
echo ""

# Example 1: Initial message
echo "Example 1: Initial message - Finding events"
echo "-------------------------------------------"

response=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}" \
  -H "Authorization: Bearer ${FIREBASE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find music concerts in New York this weekend",
    "conversation_history": [],
    "llm_provider": "openai",
    "is_initial_response": true,
    "conversation_id": null
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}Success!${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    
    # Extract conversation_id (requires jq or python)
    if command -v jq &> /dev/null; then
        CONVERSATION_ID=$(echo "$body" | jq -r '.conversation_id')
    elif command -v python3 &> /dev/null; then
        CONVERSATION_ID=$(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation_id'])" 2>/dev/null)
    else
        CONVERSATION_ID=""
    fi
    
    echo ""
    echo "Rate Limit Headers:"
    curl -s -D - -X POST "${API_ENDPOINT}" \
      -H "Authorization: Bearer ${FIREBASE_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"message": "test"}' | grep -i "x-ratelimit"
    
else
    echo -e "${RED}Error: HTTP $http_code${NC}"
    echo "$body"
fi

echo ""
echo "============================================================"

# Example 2: Continue conversation (if conversation_id was extracted)
if [ -n "$CONVERSATION_ID" ] && [ "$CONVERSATION_ID" != "null" ]; then
    echo "Example 2: Continue conversation"
    echo "-------------------------------------------"
    
    response2=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}" \
      -H "Authorization: Bearer ${FIREBASE_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"message\": \"Show me more free events\",
        \"conversation_history\": [],
        \"llm_provider\": \"openai\",
        \"is_initial_response\": false,
        \"conversation_id\": \"${CONVERSATION_ID}\"
      }")
    
    http_code2=$(echo "$response2" | tail -n1)
    body2=$(echo "$response2" | sed '$d')
    
    if [ "$http_code2" -eq 200 ]; then
        echo -e "${GREEN}Success!${NC}"
        echo "$body2" | python3 -m json.tool 2>/dev/null || echo "$body2"
    else
        echo -e "${RED}Error: HTTP $http_code2${NC}"
        echo "$body2"
    fi
    
    echo ""
    echo "============================================================"
fi

# Example 3: Error handling - Invalid token
echo "Example 3: Error handling - Invalid token"
echo "-------------------------------------------"

response3=$(curl -s -w "\n%{http_code}" -X POST "${API_ENDPOINT}" \
  -H "Authorization: Bearer invalid_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "test",
    "conversation_history": [],
    "llm_provider": "openai",
    "is_initial_response": false,
    "conversation_id": null
  }')

http_code3=$(echo "$response3" | tail -n1)
body3=$(echo "$response3" | sed '$d')

if [ "$http_code3" -eq 401 ]; then
    echo -e "${GREEN}Expected error (401 Unauthorized)${NC}"
    echo "$body3" | python3 -m json.tool 2>/dev/null || echo "$body3"
else
    echo -e "${YELLOW}Unexpected response: HTTP $http_code3${NC}"
    echo "$body3"
fi

echo ""
echo "============================================================"
echo "Examples completed!"
echo "============================================================"

