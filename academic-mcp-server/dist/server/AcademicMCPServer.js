"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AcademicMCPServer = void 0;
const index_js_1 = require("@modelcontextprotocol/sdk/server/index.js");
const types_js_1 = require("@modelcontextprotocol/sdk/types.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const events_1 = require("events");
const tools_1 = require("../tools");
const HealthCheckTool_1 = require("../tools/builtins/HealthCheckTool");
const MCPProtocolHandler_1 = require("../protocol/MCPProtocolHandler");
const MCPStreamHandler_1 = require("../protocol/MCPStreamHandler");
const MCPRequestRouter_1 = require("../protocol/MCPRequestRouter");
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
        this.toolRegistry = new tools_1.ToolRegistry({
            enableValidation: true,
            enablePermissions: false,
            enableRateLimit: true,
            maxTools: 50,
            defaultCategory: 'academic',
            ...options.toolRegistry,
        });
        this.protocolHandler = new MCPProtocolHandler_1.MCPProtocolHandler({
            serverName: this.options.name,
            serverVersion: this.options.version,
            maxConcurrentRequests: this.options.maxConnections || 10,
            capabilities: {
                tools: true,
                resources: false,
                prompts: false,
                roots: false,
            },
            ...options.protocol,
        });
        this.streamHandler = new MCPStreamHandler_1.MCPStreamHandler({
            chunkSize: 64 * 1024,
            maxConcurrentStreams: 5,
            streamTimeout: 300000,
            compressionEnabled: false,
            enableProgress: true,
            ...options.streaming,
        });
        this.requestRouter = new MCPRequestRouter_1.MCPRequestRouter({
            enableRateLimit: true,
            enableStats: true,
            enableAuth: false,
            requestTimeout: 30000,
            maxConcurrentRequests: this.options.maxConnections || 10,
            ...options.router,
        });
        this.requestRouter.setToolRegistry(this.toolRegistry);
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
        this.setupToolRegistry();
    }
    setupServerHandlers() {
        this.server.setRequestHandler(types_js_1.ListToolsRequestSchema, async () => {
            const toolsMetadata = this.toolRegistry.getAllToolsMetadata();
            const tools = {
                tools: toolsMetadata.map(metadata => ({
                    name: metadata.name,
                    description: metadata.description,
                    inputSchema: metadata.inputSchema,
                })),
            };
            this.emit('tools_listed', tools);
            return tools;
        });
        this.server.setRequestHandler(types_js_1.CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            this.emit('tool_called', { name, arguments: args });
            try {
                const context = {
                    requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    timestamp: new Date(),
                    metadata: {
                        serverName: this.options.name,
                        serverVersion: this.options.version,
                    },
                };
                const result = await this.toolRegistry.executeTool(name, args || {}, context);
                return result;
            }
            catch (error) {
                this.emit('tool_error', { name, error, arguments: args });
                throw error;
            }
        });
    }
    setupEventHandlers() {
        this.protocolHandler.on('connected', (connectionInfo) => {
            this.emit('protocol_connected', connectionInfo);
        });
        this.protocolHandler.on('disconnected', (reason) => {
            this.emit('protocol_disconnected', reason);
        });
        this.protocolHandler.on('error', (error) => {
            this.emit('protocol_error', error);
        });
        this.streamHandler.on('chunk', (chunk) => {
            this.emit('stream_chunk', chunk);
        });
        this.streamHandler.on('completed', (streamId, totalChunks) => {
            this.emit('stream_completed', { streamId, totalChunks });
        });
        this.streamHandler.on('error', (error, streamId) => {
            this.emit('stream_error', { error, streamId });
        });
        this.requestRouter.on('request-routed', (method, context) => {
            this.emit('request_routed', { method, context });
        });
        this.requestRouter.on('request-completed', (method, context, duration) => {
            this.emit('request_completed', { method, context, duration });
        });
        this.requestRouter.on('request-error', (method, context, error) => {
            this.emit('request_error', { method, context, error });
        });
        this.requestRouter.on('rate-limit-exceeded', (method, context) => {
            this.emit('rate_limit_exceeded', { method, context });
        });
    }
    setupToolRegistry() {
        this.toolRegistry.on('tool-registered', (name, metadata) => {
            this.state.registeredTools.add(name);
            this.emit('tool_registered', { name, metadata });
        });
        this.toolRegistry.on('tool-unregistered', (name) => {
            this.state.registeredTools.delete(name);
            this.emit('tool_unregistered', { name });
        });
        this.toolRegistry.on('tool-called', (name, context) => {
            this.emit('tool_executed', { name, context });
        });
        this.toolRegistry.on('tool-error', (name, error, context) => {
            this.emit('tool_execution_error', { name, error, context });
        });
        if (this.options.enableHealthCheck) {
            this.registerBuiltinTools();
        }
    }
    async registerBuiltinTools() {
        try {
            await this.toolRegistry.registerTool(HealthCheckTool_1.healthCheckTool);
        }
        catch (error) {
            console.error('Failed to register built-in tools:', error);
        }
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
    getToolRegistry() {
        return this.toolRegistry;
    }
    async registerTool(registration) {
        await this.toolRegistry.registerTool(registration);
    }
    async unregisterTool(name) {
        return this.toolRegistry.unregisterTool(name);
    }
    getRegisteredTools() {
        return this.toolRegistry.getAllToolsMetadata();
    }
    getToolRegistryStats() {
        return this.toolRegistry.getStats();
    }
    getProtocolHandler() {
        return this.protocolHandler;
    }
    getStreamHandler() {
        return this.streamHandler;
    }
    getRequestRouter() {
        return this.requestRouter;
    }
    async handleRawMessage(message) {
        try {
            const response = await this.protocolHandler.handleMessage(message);
            return response;
        }
        catch (error) {
            this.emit('protocol_error', error);
            throw error;
        }
    }
    getServerStats() {
        return {
            server: this.getState(),
            tools: this.getToolRegistryStats(),
            protocol: this.protocolHandler.getStats(),
            router: this.requestRouter.getStatus(),
            streaming: this.streamHandler.getStreamStats(),
        };
    }
    createResponseStream(data, metadata) {
        return this.streamHandler.createOutputStream(data, metadata);
    }
    async initializeProtocol(clientInfo) {
        return await this.protocolHandler.initialize(clientInfo);
    }
}
exports.AcademicMCPServer = AcademicMCPServer;
//# sourceMappingURL=AcademicMCPServer.js.map