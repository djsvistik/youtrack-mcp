#!/usr/bin/env python3
"""
HTTP Transport Wrapper for YouTrack MCP Server
This script works around the transport parameter issue by directly using FastMCP
"""
import os
import sys
import logging
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Set up paths to import from the youtrack_mcp package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtrack_mcp.config import Config, config
from youtrack_mcp.tools.loader import load_all_tools
from youtrack_mcp.version import __version__ as APP_VERSION

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global tools instance
tools = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application."""
    global tools
    
    # Load configuration
    load_config()
    
    # Load all tools
    all_tools = load_all_tools()
    tools = all_tools
    
    logger.info(f"HTTP server started with {len(all_tools)} tools")
    
    yield
    
    # Cleanup when the application is shutting down
    logger.info("Shutting down HTTP server")

# FastAPI app for HTTP mode
app = FastAPI(
    title="YouTrack MCP Server",
    description="MCP Server for JetBrains YouTrack (HTTP Transport)",
    version=APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Execute a specific tool by name."""
    try:
        # Get tool from registry
        if tool_name not in tools:
            return JSONResponse(
                status_code=404,
                content={"error": f"Tool '{tool_name}' not found"}
            )
        
        # Parse request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Execute tool
        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
        result = tools[tool_name](**arguments)
        
        return {"result": result}
    except Exception as e:
        logger.exception(f"Error executing tool {tool_name}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/tools")
async def list_tools():
    """List all available tools."""
    tool_definitions = {}
    
    for name, tool_func in tools.items():
        # Get tool metadata if available
        if hasattr(tool_func, "tool_definition"):
            tool_definitions[name] = tool_func.tool_definition
        else:
            # Basic definition if metadata not available
            tool_definitions[name] = {
                "name": name,
                "description": tool_func.__doc__ or "No description available"
            }
    
    return {"tools": tool_definitions}

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "YouTrack MCP Server",
        "version": APP_VERSION,
        "transport": "http",
        "endpoints": {
            "tools": "/api/tools",
            "execute": "/api/tools/{tool_name}"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "tools_loaded": len(tools)}

def load_config():
    """Load configuration from environment variables."""
    # Environment variables have higher priority than config file
    env_config = {}
    
    # Extract config variables from environment
    for key in dir(Config):
        if key.isupper() and not key.startswith("_"):
            env_key = f"YOUTRACK_MCP_{key}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                # Convert string booleans to actual booleans
                if env_value.lower() in ("true", "false"):
                    env_value = env_value.lower() == "true"
                env_config[key] = env_value
    
    # Create config instance from environment variables
    if env_config:
        logger.info("Loading configuration from environment variables")
        Config.from_dict(env_config)
    
    # Ensure token is properly formatted for YouTrack Cloud
    if config.YOUTRACK_API_TOKEN and not config.YOUTRACK_API_TOKEN.startswith(("perm:", "perm-")):
        # Check if we need to add the perm- prefix
        if "." in config.YOUTRACK_API_TOKEN and "=" in config.YOUTRACK_API_TOKEN:
            config.YOUTRACK_API_TOKEN = f"perm-{config.YOUTRACK_API_TOKEN}"
            logger.info("Added 'perm-' prefix to the API token")
        else:
            # For traditional tokens
            config.YOUTRACK_API_TOKEN = f"perm:{config.YOUTRACK_API_TOKEN}"
            logger.info("Added 'perm:' prefix to the API token")
    
    # Force YouTrack URL to be properly formatted
    if config.YOUTRACK_URL and config.YOUTRACK_URL.endswith("/"):
        config.YOUTRACK_URL = config.YOUTRACK_URL.rstrip("/")
        logger.info("Removed trailing slash from YouTrack URL")
    
    # Initialize configuration from environment variables
    config.validate()
    
    # Use environment variable for URL if specified instead of auto-detection
    if os.getenv("YOUTRACK_URL") and not config.YOUTRACK_URL:
        logger.info(f"Using URL from environment: {os.getenv('YOUTRACK_URL')}")
        config.YOUTRACK_URL = os.getenv("YOUTRACK_URL")
    
    # Log configuration status
    if config.YOUTRACK_URL:
        logger.info(f"Configured for YouTrack instance at: {config.YOUTRACK_URL}")
    else:
        logger.info("Configured for YouTrack Cloud instance")
    
    logger.info(f"SSL verification: {'Enabled' if config.VERIFY_SSL else 'Disabled'}")

def main():
    """Run the HTTP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTrack MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info(f"Starting YouTrack MCP HTTP Server v{APP_VERSION}")
    logger.info(f"Server will run on http://{args.host}:{args.port}")
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())

if __name__ == "__main__":
    main()