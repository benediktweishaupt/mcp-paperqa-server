import { JSONRPCMessage } from '@modelcontextprotocol/sdk/types.js';
import { EventEmitter } from 'events';
import { ToolRegistry, ToolRegistryConfig } from '../tools';
import { MCPProtocolHandler, MCPProtocolConfig } from '../protocol/MCPProtocolHandler';
import { MCPStreamHandler, StreamConfig } from '../protocol/MCPStreamHandler';
import { MCPRequestRouter, RouterConfig } from '../protocol/MCPRequestRouter';
export interface ServerState {
    isRunning: boolean;
    connections: Map<string, unknown>;
    registeredTools: Set<string>;
    startTime: Date;
}
export interface AcademicMCPServerOptions {
    name: string;
    version: string;
    description?: string;
    enableHealthCheck?: boolean;
    maxConnections?: number;
    toolRegistry?: Partial<ToolRegistryConfig>;
    protocol?: Partial<MCPProtocolConfig>;
    router?: Partial<RouterConfig>;
    streaming?: Partial<StreamConfig>;
}
export declare class AcademicMCPServer extends EventEmitter {
    private server;
    private transport;
    private state;
    private options;
    private shutdownHandlers;
    private toolRegistry;
    private protocolHandler;
    private streamHandler;
    private requestRouter;
    constructor(options: AcademicMCPServerOptions);
    private setupServerHandlers;
    private setupEventHandlers;
    private setupToolRegistry;
    private registerBuiltinTools;
    start(): Promise<void>;
    stop(): Promise<void>;
    addShutdownHandler(handler: () => Promise<void>): void;
    getState(): Readonly<ServerState>;
    getOptions(): Readonly<AcademicMCPServerOptions>;
    isRunning(): boolean;
    getUptime(): number;
    getToolRegistry(): ToolRegistry;
    registerTool(registration: import('../tools').ToolRegistration): Promise<void>;
    unregisterTool(name: string): Promise<boolean>;
    getRegisteredTools(): import('../tools').ToolMetadata[];
    getToolRegistryStats(): {
        totalTools: number;
        categoryCounts: Record<string, number>;
        deprecatedTools: string[];
        experimentalTools: string[];
    };
    getProtocolHandler(): MCPProtocolHandler;
    getStreamHandler(): MCPStreamHandler;
    getRequestRouter(): MCPRequestRouter;
    handleRawMessage(message: JSONRPCMessage): Promise<JSONRPCMessage | null>;
    getServerStats(): {
        server: Readonly<ServerState>;
        tools: {
            totalTools: number;
            categoryCounts: Record<string, number>;
            deprecatedTools: string[];
            experimentalTools: string[];
        };
        protocol: {
            messagesSent: number;
            messagesReceived: number;
            activeRequests: number;
            queuedMessages: number;
            isConnected: boolean;
            uptime: number;
        };
        router: {
            totalRoutes: number;
            activeRequests: number;
            rateLimitedMethods: string[];
            averageResponseTime: number;
        };
        streaming: {
            activeStreams: number;
            totalStreamsProcessed: number;
            averageChunkSize: number;
            longestStreamDuration: number;
        };
    };
    createResponseStream(data: unknown, metadata?: Record<string, unknown>): string;
    initializeProtocol(clientInfo?: {
        name: string;
        version: string;
    }): Promise<any>;
}
//# sourceMappingURL=AcademicMCPServer.d.ts.map