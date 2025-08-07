import { AcademicMCPServer } from './server/AcademicMCPServer';

/**
 * Academic MCP Server Entry Point
 * Initializes and starts the MCP server for academic research assistance
 */

async function main(): Promise<void> {
  // Create Academic MCP Server instance
  const server = new AcademicMCPServer({
    name: 'academic-mcp-server',
    version: '1.0.0',
    description: 'MCP server for academic research assistance with PDF processing and intelligent search',
    enableHealthCheck: true,
    maxConnections: 10,
  });

  // Set up event listeners
  server.on('started', (info) => {
    console.log(`Server started: ${info.name} v${info.version} at ${info.startTime}`);
  });

  server.on('stopped', () => {
    console.log('Server stopped');
  });

  server.on('error', (error) => {
    console.error('Server error:', error);
  });

  server.on('tool_called', (info) => {
    console.log(`Tool called: ${info.name} with args:`, info.arguments);
  });

  server.on('tool_error', (info) => {
    console.error(`Tool error in ${info.name}:`, info.error);
  });

  // Start the server
  try {
    await server.start();
    console.log('Academic MCP Server is ready for connections');
    
    // Keep the process alive
    process.on('SIGINT', async () => {
      await server.stop();
    });
    
    process.on('SIGTERM', async () => {
      await server.stop();
    });
    
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server if this file is run directly
if (require.main === module) {
  main().catch(error => {
    console.error('Startup error:', error);
    process.exit(1);
  });
}
