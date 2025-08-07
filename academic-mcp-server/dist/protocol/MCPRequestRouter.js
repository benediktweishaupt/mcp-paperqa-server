"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MCPRequestRouter = void 0;
const events_1 = require("events");
class MCPRequestRouter extends events_1.EventEmitter {
    constructor(config = {}) {
        super();
        this.routes = new Map();
        this.rateLimits = new Map();
        this.stats = new Map();
        this.activeRequests = new Map();
        this.config = {
            enableRateLimit: true,
            enableStats: true,
            enableAuth: false,
            defaultRateLimit: {
                requests: 100,
                windowMs: 60000,
            },
            requestTimeout: 30000,
            maxConcurrentRequests: 50,
            ...config,
        };
        this.registerBuiltinRoutes();
    }
    setToolRegistry(toolRegistry) {
        this.toolRegistry = toolRegistry;
    }
    registerRoute(route) {
        if (this.routes.has(route.method)) {
            throw new Error(`Route '${route.method}' is already registered`);
        }
        this.routes.set(route.method, route);
        this.emit('route-registered', route.method);
        console.log(`Route registered: ${route.method}`);
    }
    unregisterRoute(method) {
        const removed = this.routes.delete(method);
        if (removed) {
            this.rateLimits.delete(method);
            this.stats.delete(method);
            this.emit('route-unregistered', method);
            console.log(`Route unregistered: ${method}`);
        }
        return removed;
    }
    async routeRequest(request, context) {
        const startTime = Date.now();
        try {
            const route = this.routes.get(request.method);
            if (!route) {
                return this.createErrorResponse(request.id, -32601, `Method '${request.method}' not found`);
            }
            const activeCount = this.activeRequests.get(request.method) || 0;
            if (activeCount >= this.config.maxConcurrentRequests) {
                return this.createErrorResponse(request.id, -32000, 'Too many concurrent requests');
            }
            this.activeRequests.set(request.method, activeCount + 1);
            try {
                if (this.config.enableRateLimit && route.rateLimit) {
                    if (!this.checkRateLimit(request.method, route.rateLimit)) {
                        this.emit('rate-limit-exceeded', request.method, context);
                        return this.createErrorResponse(request.id, -32000, 'Rate limit exceeded');
                    }
                }
                if (this.config.enableAuth && route.requiresAuth) {
                    console.log(`Auth required for method: ${request.method}`);
                }
                this.emit('request-routed', request.method, context);
                const result = await Promise.race([
                    route.handler(request, context),
                    this.createTimeoutPromise(request.id),
                ]);
                if (this.config.enableStats) {
                    this.updateStats(request.method, Date.now() - startTime, true);
                }
                this.emit('request-completed', request.method, context, Date.now() - startTime);
                return this.createSuccessResponse(request.id, result);
            }
            finally {
                const newCount = Math.max(0, (this.activeRequests.get(request.method) || 1) - 1);
                this.activeRequests.set(request.method, newCount);
            }
        }
        catch (error) {
            if (this.config.enableStats) {
                this.updateStats(request.method, Date.now() - startTime, false);
            }
            this.emit('request-error', request.method, context, error);
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            return this.createErrorResponse(request.id, -32603, `Internal error: ${errorMessage}`);
        }
    }
    getRoutes() {
        return Array.from(this.routes.values());
    }
    getRoute(method) {
        return this.routes.get(method) || null;
    }
    hasRoute(method) {
        return this.routes.has(method);
    }
    getStats() {
        return Array.from(this.stats.values());
    }
    getMethodStats(method) {
        return this.stats.get(method) || null;
    }
    getStatus() {
        const rateLimitedMethods = Array.from(this.rateLimits.keys());
        let totalRequests = 0;
        let totalResponseTime = 0;
        let totalActiveRequests = 0;
        for (const stats of this.stats.values()) {
            totalRequests += stats.totalRequests;
            totalResponseTime += stats.averageResponseTime * stats.totalRequests;
        }
        for (const count of this.activeRequests.values()) {
            totalActiveRequests += count;
        }
        return {
            totalRoutes: this.routes.size,
            activeRequests: totalActiveRequests,
            rateLimitedMethods,
            averageResponseTime: totalRequests > 0 ? totalResponseTime / totalRequests : 0,
        };
    }
    registerBuiltinRoutes() {
        this.registerRoute({
            method: 'initialize',
            handler: async (_request) => {
                return {
                    protocolVersion: '0.1.0',
                    capabilities: {
                        tools: true,
                        resources: false,
                        prompts: false,
                    },
                    serverInfo: {
                        name: 'academic-mcp-server',
                        version: '1.0.0',
                    },
                };
            },
            metadata: {
                description: 'Initialize MCP connection',
                tags: ['core', 'initialization'],
            },
        });
        this.registerRoute({
            method: 'ping',
            handler: async () => {
                return { status: 'pong', timestamp: new Date().toISOString() };
            },
            rateLimit: { requests: 60, windowMs: 60000 },
            metadata: {
                description: 'Health check endpoint',
                tags: ['core', 'health'],
            },
        });
        this.registerRoute({
            method: 'tools/list',
            handler: async (_request, _context) => {
                if (!this.toolRegistry) {
                    throw new Error('Tool registry not configured');
                }
                const tools = this.toolRegistry.getAllToolsMetadata();
                return {
                    tools: tools.map(tool => ({
                        name: tool.name,
                        description: tool.description,
                        inputSchema: tool.inputSchema,
                    })),
                };
            },
            rateLimit: { requests: 30, windowMs: 60000 },
            metadata: {
                description: 'List available tools',
                tags: ['tools', 'discovery'],
            },
        });
        this.registerRoute({
            method: 'tools/call',
            handler: async (request, context) => {
                if (!this.toolRegistry) {
                    throw new Error('Tool registry not configured');
                }
                const { name, arguments: args } = request.params;
                if (!name) {
                    throw new Error('Tool name is required');
                }
                const toolContext = {
                    requestId: context.requestId?.toString() || 'unknown',
                    timestamp: context.timestamp,
                    metadata: context.metadata || {},
                };
                return await this.toolRegistry.executeTool(name, args || {}, toolContext);
            },
            rateLimit: { requests: 100, windowMs: 60000 },
            metadata: {
                description: 'Execute a tool',
                tags: ['tools', 'execution'],
            },
        });
        this.registerRoute({
            method: 'completion/complete',
            handler: async (_request) => {
                return {
                    completion: {
                        values: [],
                        total: 0,
                    },
                };
            },
            rateLimit: { requests: 10, windowMs: 60000 },
            metadata: {
                description: 'Get completion suggestions',
                tags: ['completion'],
            },
        });
    }
    checkRateLimit(method, rateLimit) {
        const now = Date.now();
        let state = this.rateLimits.get(method);
        if (!state || now > state.resetTime) {
            state = {
                method,
                requests: 1,
                resetTime: now + rateLimit.windowMs,
            };
            this.rateLimits.set(method, state);
            return true;
        }
        if (state.requests >= rateLimit.requests) {
            return false;
        }
        state.requests++;
        this.rateLimits.set(method, state);
        return true;
    }
    updateStats(method, responseTime, success) {
        let stats = this.stats.get(method);
        if (!stats) {
            stats = {
                method,
                totalRequests: 0,
                successfulRequests: 0,
                failedRequests: 0,
                averageResponseTime: 0,
                lastRequestTime: new Date(),
            };
        }
        stats.totalRequests++;
        if (success) {
            stats.successfulRequests++;
        }
        else {
            stats.failedRequests++;
        }
        stats.averageResponseTime = ((stats.averageResponseTime * (stats.totalRequests - 1) + responseTime) /
            stats.totalRequests);
        stats.lastRequestTime = new Date();
        this.stats.set(method, stats);
    }
    createTimeoutPromise(requestId) {
        return new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error(`Request ${requestId} timed out after ${this.config.requestTimeout}ms`));
            }, this.config.requestTimeout);
        });
    }
    createSuccessResponse(id, result) {
        return {
            jsonrpc: '2.0',
            id,
            result: result,
        };
    }
    createErrorResponse(id, code, message) {
        return {
            jsonrpc: '2.0',
            id,
            error: {
                code,
                message,
            },
        };
    }
    clearStats() {
        this.stats.clear();
        this.rateLimits.clear();
        this.activeRequests.clear();
    }
    getConfig() {
        return { ...this.config };
    }
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    emit(event, ...args) {
        return super.emit(event, ...args);
    }
    on(event, listener) {
        return super.on(event, listener);
    }
    off(event, listener) {
        return super.off(event, listener);
    }
}
exports.MCPRequestRouter = MCPRequestRouter;
//# sourceMappingURL=MCPRequestRouter.js.map