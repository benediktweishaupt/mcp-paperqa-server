# MCP Servers

## Figma Dev Mode MCP Rules

- The Figma Dev Mode MCP Server provides an assets endpoint which can serve image and SVG assets
- IMPORTANT: If the Figma Dev Mode MCP Server returns a localhost source for an image or an SVG, use that image or SVG source directly
- IMPORTANT: DO NOT import/add new icon packages, all the assets should be in the Figma payload
- IMPORTANT: do NOT use or create placeholders if a localhost source is provided

How to install figma MCP server:
claude mcp add --transport sse figma-dev-mode-mcp-server http://127.0.0.1:3845/sse

Source:https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Dev-Mode-MCP-Server#:~:text=Windsurf-,Claude,-Code

Context 7 MCP Server:
claude mcp add context7 -- npx -y @upstash/context7-mcp

Source:
https://github.com/upstash/context7#:~:text=Install%20in-,Claude,-Code

Task Master
Option 2: Using Command Line
Installation

# Install globally

npm install -g task-master-ai

# If installed globally

task-master init

put in the config.json:
{
"models": {
"main": {
"provider": "claude-code",
"modelId": "sonnet",
"maxTokens": 64000,
"temperature": 0.2
},
"research": {
"provider": "claude-code",
"modelId": "opus",
"maxTokens": 32000,
"temperature": 0.1
},
"fallback": {
"provider": "claude-code",
"modelId": "sonnet",
"maxTokens": 64000,
"temperature": 0.2
}
}
}
