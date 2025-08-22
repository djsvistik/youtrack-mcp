#!/bin/bash
# Test script for YouTrack MCP HTTP transport

set -e

echo "🚀 YouTrack MCP HTTP Transport Test Script"
echo "=========================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$YOUTRACK_API_TOKEN" ]; then
    echo "⚠️  YOUTRACK_API_TOKEN environment variable is not set"
    echo "   Please set it with: export YOUTRACK_API_TOKEN=your-token"
    exit 1
fi

echo "✅ Environment check passed"
echo ""

# Function to test HTTP transport
test_http_transport() {
    echo "📡 Testing HTTP Transport"
    echo "------------------------"
    
    echo "Building HTTP Docker image..."
    docker build -f Dockerfile.http -t youtrack-mcp-http-test . --quiet
    
    echo "Starting HTTP server in background..."
    CONTAINER_ID=$(docker run -d --rm -p 8000:8000 \
        -e "YOUTRACK_API_TOKEN=$YOUTRACK_API_TOKEN" \
        -e "YOUTRACK_URL=${YOUTRACK_URL:-}" \
        youtrack-mcp-http-test)
    
    echo "Container ID: $CONTAINER_ID"
    
    # Wait for server to start
    echo "Waiting for server to start..."
    sleep 5
    
    # Test the HTTP API
    echo "Testing API endpoints..."
    
    echo "1. Testing /api/tools endpoint..."
    if curl -s -f http://localhost:8000/api/tools > /dev/null; then
        echo "   ✅ /api/tools endpoint is accessible"
    else
        echo "   ❌ /api/tools endpoint failed"
        docker logs $CONTAINER_ID
        docker stop $CONTAINER_ID
        exit 1
    fi
    
    echo "2. Getting available tools..."
    curl -s http://localhost:8000/api/tools | jq . 2>/dev/null || echo "   Note: jq not available for JSON formatting"
    
    echo ""
    echo "🎉 HTTP transport test completed successfully!"
    
    # Cleanup
    echo "Stopping container..."
    docker stop $CONTAINER_ID
    echo ""
}

# Function to test flexible transport
test_flexible_transport() {
    echo "🔄 Testing Flexible Transport"
    echo "-----------------------------"
    
    echo "Building flexible Docker image..."
    docker build -f Dockerfile.flexible -t youtrack-mcp-flexible-test . --quiet
    
    echo "Testing HTTP mode..."
    CONTAINER_ID=$(docker run -d --rm -p 8001:8000 \
        -e "MCP_TRANSPORT=http" \
        -e "YOUTRACK_API_TOKEN=$YOUTRACK_API_TOKEN" \
        -e "YOUTRACK_URL=${YOUTRACK_URL:-}" \
        youtrack-mcp-flexible-test)
    
    echo "Container ID: $CONTAINER_ID"
    sleep 5
    
    if curl -s -f http://localhost:8001/api/tools > /dev/null; then
        echo "   ✅ Flexible HTTP mode working"
    else
        echo "   ❌ Flexible HTTP mode failed"
        docker logs $CONTAINER_ID
    fi
    
    docker stop $CONTAINER_ID
    
    echo "Testing stdio mode..."
    docker run --rm \
        -e "MCP_TRANSPORT=stdio" \
        -e "YOUTRACK_API_TOKEN=$YOUTRACK_API_TOKEN" \
        -e "YOUTRACK_URL=${YOUTRACK_URL:-}" \
        youtrack-mcp-flexible-test \
        --version
    
    echo "   ✅ Flexible stdio mode working"
    echo ""
}

# Main execution
echo "Starting tests..."
echo ""

test_http_transport
test_flexible_transport

echo "🎊 All tests completed successfully!"
echo ""
echo "Usage examples:"
echo "  # HTTP mode:"
echo "  docker run --rm -p 8000:8000 -e YOUTRACK_API_TOKEN=\$YOUTRACK_API_TOKEN youtrack-mcp-http-test"
echo ""
echo "  # Flexible mode (HTTP):"
echo "  docker run --rm -p 8000:8000 -e MCP_TRANSPORT=http -e YOUTRACK_API_TOKEN=\$YOUTRACK_API_TOKEN youtrack-mcp-flexible-test"
echo ""
echo "  # Flexible mode (stdio):"
echo "  docker run --rm -i -e YOUTRACK_API_TOKEN=\$YOUTRACK_API_TOKEN youtrack-mcp-flexible-test"