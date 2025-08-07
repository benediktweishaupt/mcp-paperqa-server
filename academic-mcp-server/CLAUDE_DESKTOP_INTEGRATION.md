# Claude Desktop Integration

This document describes how to integrate the Academic MCP Server with Claude Desktop.

## Quick Setup

1. **Build the server:**
   ```bash
   npm run build
   ```

2. **Copy configuration to Claude Desktop:**
   
   On macOS, Claude Desktop configuration is located at:
   `~/Library/Application Support/Claude/claude_desktop_config.json`

   Copy the contents of either configuration file:
   - `claude-desktop-config.json` (production)
   - `claude-desktop-config.dev.json` (development)

3. **Restart Claude Desktop** to load the new MCP server.

## Configuration Options

### Production Configuration

```json
{
  "mcpServers": {
    "academic-research-assistant": {
      "command": "node",
      "args": ["./dist/index.js"],
      "cwd": "/path/to/academic-mcp-server",
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### Development Configuration

```json
{
  "mcpServers": {
    "academic-research-assistant": {
      "command": "npm",
      "args": ["run", "dev"],
      "cwd": "/path/to/academic-mcp-server",
      "env": {
        "NODE_ENV": "development",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

## Available Tools

Once connected, the following MCP tools will be available in Claude Desktop:

### Core Tools
- **health_check**: Server health and status check
- **initialize**: Initialize MCP connection
- **ping**: Health check endpoint

### Future Tools (Phase 2+)
- **pdf_search**: Search across PDF documents
- **citation_extract**: Extract citations from PDFs
- **argument_track**: Track arguments across multiple sources
- **research_gaps**: Identify gaps in literature coverage

## Troubleshooting

### Server Won't Start
1. Ensure all dependencies are installed: `npm install`
2. Build the project: `npm run build`
3. Check that the `cwd` path in the configuration is correct

### Connection Issues
1. Check Claude Desktop logs (usually in Claude app menu → View Logs)
2. Verify the MCP server is running correctly: `npm start`
3. Ensure no other process is using the same port

### Development Mode
For active development, use the development configuration which will:
- Restart automatically on file changes (via nodemon)
- Provide detailed debug logs
- Use TypeScript directly without compilation step

## Manual Testing

You can test the MCP server manually:

```bash
# Start in development mode
npm run dev

# Or start built version
npm start
```

The server will output connection information and available tools when started successfully.

## Environment Variables

The server supports the following environment variables:

- `NODE_ENV`: Set to 'development' or 'production'
- `LOG_LEVEL`: Set logging level (error, warn, info, debug)
- `MCP_SERVER_PORT`: Override default port (if applicable)

## Integration Status

- ✅ Basic MCP protocol implementation
- ✅ Tool registration framework
- ✅ Error handling and logging
- ✅ Claude Desktop configuration
- ⏳ PDF processing tools (Phase 2)
- ⏳ Search and analysis tools (Phase 2)