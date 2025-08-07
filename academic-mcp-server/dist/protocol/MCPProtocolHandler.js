"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MCPProtocolHandler = void 0;
const events_1 = require("events");
class MCPProtocolHandler extends events_1.EventEmitter {
    constructor(config = {}) {
        super();
        this.messageQueue = new Map();
        this.activeRequests = new Map();
        this.requestIdCounter = 0;
        this.config = {
            serverName: 'academic-mcp-server',
            serverVersion: '1.0.0',
            maxConcurrentRequests: 10,
            requestTimeout: 30000,
            enableMessageQueue: true,
            queueMaxSize: 100,
            maxRetries: 3,
            supportedMethods: [
                'initialize',
                'tools/list',
                'tools/call',
                'ping',
                'completion/complete'
            ],
            capabilities: {
                tools: true,
                resources: false,
                prompts: false,
                roots: false,
            },
            ...config,
        };
        this.connectionState = {
            isConnected: false,
            serverInfo: {
                name: this.config.serverName,
                version: this.config.serverVersion,
            },
            lastActivity: new Date(),
            messagesSent: 0,
            messagesReceived: 0,
        };
    }
    async initialize(clientInfo) {
        this.connectionState.isConnected = true;
        this.connectionState.clientInfo = clientInfo;
        this.connectionState.version = {
            version: this.config.serverVersion,
            capabilities: this.config.capabilities,
        };
        this.connectionState.lastActivity = new Date();
        this.emit('connected', this.connectionState);
        return {
            version: this.config.serverVersion,
            capabilities: this.config.capabilities,
        };
    }
    async handleMessage(message) {
        this.connectionState.messagesReceived++;
        this.connectionState.lastActivity = new Date();
        this.emit('message-received', message);
        try {
            const validationResult = this.validateMessage(message);
            if (!validationResult.valid) {
                if ('id' in message && message.id !== undefined) {
                    return this.createErrorResponse(message.id, -32600, validationResult.error || 'Invalid Request');
                }
                return null;
            }
            if (this.isRequest(message)) {
                this.emit('request', message);
                return await this.handleRequest(message);
            }
            else if (this.isResponse(message)) {
                this.emit('response', message);
                this.handleResponse(message);
                return null;
            }
            else if (this.isNotification(message)) {
                this.emit('notification', message);
                await this.handleNotification(message);
                return null;
            }
            if ('id' in message && message.id !== undefined) {
                return this.createErrorResponse(message.id, -32600, 'Invalid Request');
            }
            return null;
        }
        catch (error) {
            this.emit('error', error);
            if ('id' in message && message.id !== undefined) {
                return this.createErrorResponse(message.id, -32603, 'Internal error');
            }
            return null;
        }
    }
    async sendRequest(method, params, timeout) {
        const id = ++this.requestIdCounter;
        const request = {
            jsonrpc: '2.0',
            id,
            method,
            params: params,
        };
        return new Promise((resolve, reject) => {
            const timeoutMs = timeout || this.config.requestTimeout;
            const timeoutHandle = setTimeout(() => {
                this.activeRequests.delete(id);
                reject(new Error(`Request timeout after ${timeoutMs}ms`));
            }, timeoutMs);
            this.activeRequests.set(id, timeoutHandle);
            this.sendMessage(request);
            const originalResolver = resolve;
            this.activeRequests.set(id, {
                ...timeoutHandle,
                resolve: originalResolver,
                reject,
            });
        });
    }
    sendNotification(method, params) {
        const notification = {
            jsonrpc: '2.0',
            method,
            params: params,
        };
        this.sendMessage(notification);
    }
    sendResponse(id, result, error) {
        const response = {
            jsonrpc: '2.0',
            id,
        };
        if (error) {
            response.error = error;
        }
        else {
            response.result = result;
        }
        this.sendMessage(response);
    }
    sendMessage(message) {
        this.connectionState.messagesSent++;
        this.connectionState.lastActivity = new Date();
        this.emit('message-sent', message);
        console.log('Sending message:', JSON.stringify(message, null, 2));
    }
    async handleRequest(request) {
        try {
            if (!this.config.supportedMethods.includes(request.method)) {
                return this.createErrorResponse(request.id, -32601, `Method '${request.method}' not found`);
            }
            switch (request.method) {
                case 'initialize':
                    const initResult = await this.handleInitialize(request.params);
                    return this.createSuccessResponse(request.id, initResult);
                case 'ping':
                    return this.createSuccessResponse(request.id, { status: 'pong' });
                case 'tools/list':
                    return this.createErrorResponse(request.id, -32601, 'Method should be handled by server');
                case 'tools/call':
                    return this.createErrorResponse(request.id, -32601, 'Method should be handled by server');
                default:
                    return this.createErrorResponse(request.id, -32601, `Unknown method: ${request.method}`);
            }
        }
        catch (error) {
            return this.createErrorResponse(request.id, -32603, `Internal error: ${error.message}`);
        }
    }
    handleResponse(response) {
        const requestInfo = this.activeRequests.get(response.id);
        if (requestInfo) {
            this.activeRequests.delete(response.id);
            if (typeof requestInfo === 'object' && 'resolve' in requestInfo) {
                clearTimeout(requestInfo);
                if (response.error) {
                    requestInfo.reject(new Error(response.error.message));
                }
                else {
                    requestInfo.resolve(response);
                }
            }
        }
    }
    async handleNotification(notification) {
        switch (notification.method) {
            case 'notifications/cancelled':
                break;
            case 'notifications/progress':
                break;
            default:
                console.log(`Unhandled notification: ${notification.method}`);
        }
    }
    async handleInitialize(params) {
        const clientInfo = params;
        if (clientInfo?.clientInfo) {
            this.connectionState.clientInfo = clientInfo.clientInfo;
        }
        return {
            version: this.config.serverVersion,
            capabilities: this.config.capabilities || {},
        };
    }
    validateMessage(message) {
        if (!message || typeof message !== 'object') {
            return { valid: false, error: 'Message must be an object' };
        }
        if (message.jsonrpc !== '2.0') {
            return { valid: false, error: 'Invalid JSON-RPC version' };
        }
        if (!message.method && !('result' in message) && !('error' in message)) {
            return { valid: false, error: 'Message must have method, result, or error' };
        }
        if (message.method && typeof message.method !== 'string') {
            return { valid: false, error: 'Method must be a string' };
        }
        if ('id' in message && message.id !== null && typeof message.id !== 'string' && typeof message.id !== 'number') {
            return { valid: false, error: 'ID must be string, number, or null' };
        }
        return { valid: true };
    }
    isRequest(message) {
        return 'method' in message && 'id' in message && message.id !== undefined;
    }
    isResponse(message) {
        return 'id' in message && ('result' in message || 'error' in message);
    }
    isNotification(message) {
        return 'method' in message && !('id' in message);
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
    getConnectionState() {
        return { ...this.connectionState };
    }
    getConfig() {
        return { ...this.config };
    }
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    async disconnect(reason) {
        this.connectionState.isConnected = false;
        for (const [_id, requestInfo] of this.activeRequests.entries()) {
            if (typeof requestInfo === 'object' && 'reject' in requestInfo) {
                clearTimeout(requestInfo);
                requestInfo.reject(new Error('Connection closed'));
            }
        }
        this.activeRequests.clear();
        this.messageQueue.clear();
        this.emit('disconnected', reason);
    }
    getStats() {
        const now = new Date();
        const startTime = this.connectionState.lastActivity;
        return {
            messagesSent: this.connectionState.messagesSent,
            messagesReceived: this.connectionState.messagesReceived,
            activeRequests: this.activeRequests.size,
            queuedMessages: this.messageQueue.size,
            isConnected: this.connectionState.isConnected,
            uptime: now.getTime() - startTime.getTime(),
        };
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
exports.MCPProtocolHandler = MCPProtocolHandler;
//# sourceMappingURL=MCPProtocolHandler.js.map