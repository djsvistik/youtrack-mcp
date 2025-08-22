# YouTrack MCP HTTP Transport

This document describes how to use YouTrack MCP server with HTTP transport using Docker.

## Available Docker Configurations

### 1. HTTP-Only Dockerfile (`Dockerfile.http`)

A dedicated Dockerfile that runs the server in HTTP mode by default.

```bash
# Build the HTTP image
docker build -f Dockerfile.http -t youtrack-mcp-http .

# Run the HTTP server
docker run --rm -p 8000:8000 \
  -e "YOUTRACK_API_TOKEN=your-token" \
  -e "YOUTRACK_URL=https://your.youtrack.cloud" \
  youtrack-mcp-http
```

### 2. Flexible Dockerfile (`Dockerfile.flexible`)

A flexible Dockerfile that supports both stdio and HTTP modes via environment variables.

```bash
# Build the flexible image
docker build -f Dockerfile.flexible -t youtrack-mcp-flexible .

# Run in HTTP mode
docker run --rm -p 8000:8000 \
  -e "MCP_TRANSPORT=http" \
  -e "YOUTRACK_API_TOKEN=your-token" \
  -e "YOUTRACK_URL=https://your.youtrack.cloud" \
  youtrack-mcp-flexible

# Run in stdio mode (default)
docker run --rm -i \
  -e "YOUTRACK_API_TOKEN=your-token" \
  -e "YOUTRACK_URL=https://your.youtrack.cloud" \
  youtrack-mcp-flexible
```

## Environment Variables

### HTTP Transport Configuration
- `MCP_TRANSPORT`: Set to "http" for HTTP mode, "stdio" for stdio mode (default: "stdio")
- `MCP_HOST`: Host to bind the HTTP server to (default: "0.0.0.0")

### YouTrack Configuration
- `YOUTRACK_API_TOKEN`: Your YouTrack API token (required)
- `YOUTRACK_URL`: Your YouTrack instance URL (optional for YouTrack Cloud)
- `YOUTRACK_VERIFY_SSL`: Verify SSL certificates (default: "true")

### Server Configuration
- `MCP_SERVER_NAME`: Server name (default: "youtrack-mcp")
- `MCP_SERVER_DESCRIPTION`: Server description (default: "YouTrack MCP Server")
- `MCP_DEBUG`: Enable debug mode (default: "false")

## Testing HTTP Transport

Once the server is running in HTTP mode, you can test it:

```bash
# List available tools
curl http://localhost:8000/api/tools

# Execute a tool (example)
curl -X POST http://localhost:8000/api/tools/get_projects \
  -H "Content-Type: application/json" \
  -d '{"arguments": {}}'
```

## Port Information

The HTTP server is hardcoded to use port 8000 in the Python application. When running with Docker:
- Container port: 8000
- Host port: configurable via `-p` option (e.g., `-p 8080:8000` to expose on host port 8080)

## Integration Examples

### Docker Compose Example

```yaml
version: '3.8'
services:
  youtrack-mcp:
    build:
      context: .
      dockerfile: Dockerfile.http
    ports:
      - "8000:8000"
    environment:
      - YOUTRACK_API_TOKEN=your-token
      - YOUTRACK_URL=https://your.youtrack.cloud
      - YOUTRACK_VERIFY_SSL=true
```

### Kubernetes Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: youtrack-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: youtrack-mcp
  template:
    metadata:
      labels:
        app: youtrack-mcp
    spec:
      containers:
      - name: youtrack-mcp
        image: youtrack-mcp-http
        ports:
        - containerPort: 8000
        env:
        - name: YOUTRACK_API_TOKEN
          value: "your-token"
        - name: YOUTRACK_URL
          value: "https://your.youtrack.cloud"
---
apiVersion: v1
kind: Service
metadata:
  name: youtrack-mcp-service
spec:
  selector:
    app: youtrack-mcp
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
```

## Security Considerations

When running in HTTP mode:
1. The server exposes HTTP endpoints without authentication
2. Consider running behind a reverse proxy with authentication
3. Use HTTPS in production environments
4. Limit network access to trusted sources
5. Keep your YouTrack API token secure