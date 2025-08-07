import { EventEmitter } from 'events';
import { JSONRPCMessage, JSONRPCRequest, JSONRPCResponse } from '@modelcontextprotocol/sdk/types.js';
export interface MCPVersion {
    version: string;
    capabilities?: {
        tools?: boolean;
        resources?: boolean;
        prompts?: boolean;
        roots?: boolean;
    } | undefined;
}
export interface MCPConnectionState {
    isConnected: boolean;
    version?: MCPVersion;
    clientInfo?: {
        name: string;
        version: string;
    } | undefined;
    serverInfo: {
        name: string;
        version: string;
    };
    lastActivity: Date;
    messagesSent: number;
    messagesReceived: number;
}
export interface MCPProtocolEvents {
    'connected': (connectionInfo: MCPConnectionState) => void;
    'disconnected': (reason?: string) => void;
    'message-received': (message: JSONRPCMessage) => void;
    'message-sent': (message: JSONRPCMessage) => void;
    'error': (error: Error) => void;
    'request': (request: JSONRPCRequest) => void;
    'response': (response: JSONRPCResponse) => void;
    'notification': (notification: JSONRPCMessage) => void;
}
export interface MCPRequestContext {
    requestId: string | number | null;
    method: string;
    timestamp: Date;
    clientId?: string;
    metadata?: Record<string, unknown>;
}
export interface MCPProtocolConfig {
    serverName: string;
    serverVersion: string;
    maxConcurrentRequests: number;
    requestTimeout: number;
    enableMessageQueue: boolean;
    queueMaxSize: number;
    maxRetries: number;
    supportedMethods: string[];
    capabilities: MCPVersion['capabilities'];
}
export declare class MCPProtocolHandler extends EventEmitter {
    private config;
    private connectionState;
    private messageQueue;
    private activeRequests;
    private requestIdCounter;
    constructor(config?: Partial<MCPProtocolConfig>);
    initialize(clientInfo?: {
        name: string;
        version: string;
    }): Promise<MCPVersion>;
    handleMessage(message: JSONRPCMessage): Promise<any | null>;
    sendRequest(method: string, params?: unknown, timeout?: number): Promise<any>;
    sendNotification(method: string, params?: unknown): void;
    sendResponse(id: string | number, result?: unknown, error?: any): void;
    protected sendMessage(message: JSONRPCMessage): void;
    private handleRequest;
    private handleResponse;
    private handleNotification;
    private handleInitialize;
    private validateMessage;
    private isRequest;
    private isResponse;
    private isNotification;
    private createSuccessResponse;
    private createErrorResponse;
    getConnectionState(): Readonly<MCPConnectionState>;
    getConfig(): Readonly<MCPProtocolConfig>;
    updateConfig(newConfig: Partial<MCPProtocolConfig>): void;
    disconnect(reason?: string): Promise<void>;
    getStats(): {
        messagesSent: number;
        messagesReceived: number;
        activeRequests: number;
        queuedMessages: number;
        isConnected: boolean;
        uptime: number;
    };
    emit<K extends keyof MCPProtocolEvents>(event: K, ...args: Parameters<MCPProtocolEvents[K]>): boolean;
    on<K extends keyof MCPProtocolEvents>(event: K, listener: MCPProtocolEvents[K]): this;
    off<K extends keyof MCPProtocolEvents>(event: K, listener: MCPProtocolEvents[K]): this;
}
//# sourceMappingURL=MCPProtocolHandler.d.ts.map