import { EventEmitter } from 'events';
import { JSONRPCRequest, JSONRPCResponse } from '@modelcontextprotocol/sdk/types.js';
import { ToolRegistry } from '../tools/ToolRegistry.js';
import { MCPRequestContext } from './MCPProtocolHandler.js';
export type RouteHandler = (request: JSONRPCRequest, context: MCPRequestContext) => Promise<unknown>;
export interface RouteInfo {
    method: string;
    handler: RouteHandler;
    requiresAuth?: boolean;
    rateLimit?: {
        requests: number;
        windowMs: number;
    };
    metadata?: {
        description?: string;
        tags?: string[];
        deprecated?: boolean;
    };
}
export interface RequestRouterEvents {
    'route-registered': (method: string) => void;
    'route-unregistered': (method: string) => void;
    'request-routed': (method: string, context: MCPRequestContext) => void;
    'request-completed': (method: string, context: MCPRequestContext, duration: number) => void;
    'request-error': (method: string, context: MCPRequestContext, error: Error) => void;
    'rate-limit-exceeded': (method: string, context: MCPRequestContext) => void;
}
interface RequestStats {
    method: string;
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    averageResponseTime: number;
    lastRequestTime: Date;
}
export interface RouterConfig {
    enableRateLimit: boolean;
    enableStats: boolean;
    enableAuth: boolean;
    defaultRateLimit?: {
        requests: number;
        windowMs: number;
    };
    requestTimeout: number;
    maxConcurrentRequests: number;
}
export declare class MCPRequestRouter extends EventEmitter {
    private config;
    private routes;
    private rateLimits;
    private stats;
    private activeRequests;
    private toolRegistry?;
    constructor(config?: Partial<RouterConfig>);
    setToolRegistry(toolRegistry: ToolRegistry): void;
    registerRoute(route: RouteInfo): void;
    unregisterRoute(method: string): boolean;
    routeRequest(request: JSONRPCRequest, context: MCPRequestContext): Promise<JSONRPCResponse>;
    getRoutes(): RouteInfo[];
    getRoute(method: string): RouteInfo | null;
    hasRoute(method: string): boolean;
    getStats(): RequestStats[];
    getMethodStats(method: string): RequestStats | null;
    getStatus(): {
        totalRoutes: number;
        activeRequests: number;
        rateLimitedMethods: string[];
        averageResponseTime: number;
    };
    private registerBuiltinRoutes;
    private checkRateLimit;
    private updateStats;
    private createTimeoutPromise;
    private createSuccessResponse;
    private createErrorResponse;
    clearStats(): void;
    getConfig(): Readonly<RouterConfig>;
    updateConfig(newConfig: Partial<RouterConfig>): void;
    emit<K extends keyof RequestRouterEvents>(event: K, ...args: Parameters<RequestRouterEvents[K]>): boolean;
    on<K extends keyof RequestRouterEvents>(event: K, listener: RequestRouterEvents[K]): this;
    off<K extends keyof RequestRouterEvents>(event: K, listener: RequestRouterEvents[K]): this;
}
export {};
//# sourceMappingURL=MCPRequestRouter.d.ts.map