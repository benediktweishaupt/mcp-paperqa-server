"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const AcademicMCPServer_1 = require("./server/AcademicMCPServer");
async function main() {
    const server = new AcademicMCPServer_1.AcademicMCPServer({
        name: 'academic-mcp-server',
        version: '1.0.0',
        description: 'MCP server for academic research assistance with PDF processing and intelligent search',
        enableHealthCheck: true,
        maxConnections: 10,
    });
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
    try {
        await server.start();
        console.log('Academic MCP Server is ready for connections');
        process.on('SIGINT', async () => {
            await server.stop();
        });
        process.on('SIGTERM', async () => {
            await server.stop();
        });
    }
    catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
}
if (require.main === module) {
    main().catch(error => {
        console.error('Startup error:', error);
        process.exit(1);
    });
}
//# sourceMappingURL=index.js.map