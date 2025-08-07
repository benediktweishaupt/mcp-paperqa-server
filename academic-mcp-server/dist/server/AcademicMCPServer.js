"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AcademicMCPServer = void 0;
const index_js_1 = require("@modelcontextprotocol/sdk/server/index.js");
const types_js_1 = require("@modelcontextprotocol/sdk/types.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const events_1 = require("events");
class AcademicMCPServer extends events_1.EventEmitter {
    constructor(options) {
        super();
        this.transport = null;
        this.shutdownHandlers = [];
        this.options = {
            enableHealthCheck: true,
            maxConnections: 10,
            ...options,
        };
        this.state = {
            isRunning: false,
            connections: new Map(),
            registeredTools: new Set(),
            startTime: new Date(),
        };
        this.server = new index_js_1.Server({
            name: this.options.name,
            version: this.options.version,
            description: this.options.description,
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.setupServerHandlers();
        this.setupEventHandlers();
    }
    setupServerHandlers() {
        this.server.setRequestHandler(types_js_1.ListToolsRequestSchema, async () => {
            const tools = {
                tools: [
                    {
                        name: 'health_check',
                        description: 'Check server health status',
                        inputSchema: {
                            type: 'object',
                            properties: {},
                            required: [],
                        },
                    },
                ],
            };
            this.emit('tools_listed', tools);
            return tools;
        });
        this.server.setRequestHandler(types_js_1.CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            this.emit('tool_called', { name, arguments: args });
            try {
                const result = await this.handleToolCall(name, args || {});
                return result;
            }
            catch (error) {
                this.emit('tool_error', { name, error, arguments: args });
                throw error;
            }
        });
    }
    setupEventHandlers() {
    }
    async handleToolCall(name, _args) {
        switch (name) {
            case 'health_check':
                return this.handleHealthCheck();
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    }
    handleHealthCheck() {
        const uptime = Date.now() - this.state.startTime.getTime();
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        status: 'healthy',
                        uptime: uptime,
                        connections: this.state.connections.size,
                        tools: this.state.registeredTools.size,
                        memory: process.memoryUsage(),
                        timestamp: new Date().toISOString(),
                    }, null, 2),
                },
            ],
        };
    }
    async start() {
        if (this.state.isRunning) {
            throw new Error('Server is already running');
        }
        try {
            this.transport = new stdio_js_1.StdioServerTransport();
            await this.server.connect(this.transport);
            this.state.isRunning = true;
            this.state.startTime = new Date();
            this.emit('started', {
                name: this.options.name,
                version: this.options.version,
                startTime: this.state.startTime,
            });
        }
        catch (error) {
            this.emit('error', error);
            throw new Error(`Failed to start server: ${error}`);
        }
    }
    async stop() {
        if (!this.state.isRunning) {
            return;
        }
        try {
            for (const handler of this.shutdownHandlers) {
                await handler();
            }
            if (this.transport) {
                await this.server.close();
                this.transport = null;
            }
            this.state.isRunning = false;
            this.state.connections.clear();
            this.emit('stopped');
        }
        catch (error) {
            this.emit('error', error);
            throw new Error(`Error during server shutdown: ${error}`);
        }
    }
    addShutdownHandler(handler) {
        this.shutdownHandlers.push(handler);
    }
    getState() {
        return { ...this.state };
    }
    getOptions() {
        return { ...this.options };
    }
    isRunning() {
        return this.state.isRunning;
    }
    getUptime() {
        return Date.now() - this.state.startTime.getTime();
    }
}
exports.AcademicMCPServer = AcademicMCPServer;
//# sourceMappingURL=AcademicMCPServer.js.map