import { EventEmitter } from 'events';
import { JSONRPCRequest, JSONRPCResponse } from '@modelcontextprotocol/sdk/types.js';
import { ToolRegistry } from '../tools/ToolRegistry.js';
import { MCPRequestContext } from './MCPProtocolHandler.js';

/**
 * Route Handler Function
 */
export type RouteHandler = (
  request: JSONRPCRequest,
  context: MCPRequestContext
) => Promise<unknown>;

/**
 * Route Information
 */
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

/**
 * Request Router Events
 */
export interface RequestRouterEvents {
  'route-registered': (method: string) => void;
  'route-unregistered': (method: string) => void;
  'request-routed': (method: string, context: MCPRequestContext) => void;
  'request-completed': (method: string, context: MCPRequestContext, duration: number) => void;
  'request-error': (method: string, context: MCPRequestContext, error: Error) => void;
  'rate-limit-exceeded': (method: string, context: MCPRequestContext) => void;
}

/**
 * Rate Limiting State
 */
interface RateLimitState {
  method: string;
  requests: number;
  resetTime: number;
}

/**
 * Request Statistics
 */
interface RequestStats {
  method: string;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  lastRequestTime: Date;
}

/**
 * Router Configuration
 */
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

/**
 * MCP Request Router
 * Routes JSON-RPC requests to appropriate handlers
 */
export class MCPRequestRouter extends EventEmitter {
  private config: RouterConfig;
  private routes = new Map<string, RouteInfo>();
  private rateLimits = new Map<string, RateLimitState>();
  private stats = new Map<string, RequestStats>();
  private activeRequests = new Map<string, number>();
  private toolRegistry?: ToolRegistry;

  constructor(config: Partial<RouterConfig> = {}) {
    super();
    
    this.config = {
      enableRateLimit: true,
      enableStats: true,
      enableAuth: false,
      defaultRateLimit: {
        requests: 100,
        windowMs: 60000, // 1 minute
      },
      requestTimeout: 30000,
      maxConcurrentRequests: 50,
      ...config,
    };

    // Register built-in routes
    this.registerBuiltinRoutes();
  }

  /**
   * Set tool registry for tool-related routes
   */
  setToolRegistry(toolRegistry: ToolRegistry): void {
    this.toolRegistry = toolRegistry;
  }

  /**
   * Register a route handler
   */
  registerRoute(route: RouteInfo): void {
    if (this.routes.has(route.method)) {
      throw new Error(`Route '${route.method}' is already registered`);
    }

    this.routes.set(route.method, route);
    this.emit('route-registered', route.method);

    console.log(`Route registered: ${route.method}`);
  }

  /**
   * Unregister a route handler
   */
  unregisterRoute(method: string): boolean {
    const removed = this.routes.delete(method);
    if (removed) {
      this.rateLimits.delete(method);
      this.stats.delete(method);
      this.emit('route-unregistered', method);
      console.log(`Route unregistered: ${method}`);
    }
    return removed;
  }

  /**
   * Route an incoming request
   */
  async routeRequest(request: JSONRPCRequest, context: MCPRequestContext): Promise<JSONRPCResponse> {
    const startTime = Date.now();

    try {
      // Check if route exists
      const route = this.routes.get(request.method);
      if (!route) {
        return this.createErrorResponse(request.id, -32601, `Method '${request.method}' not found`);
      }

      // Check concurrent request limit
      const activeCount = this.activeRequests.get(request.method) || 0;
      if (activeCount >= this.config.maxConcurrentRequests) {
        return this.createErrorResponse(request.id, -32000, 'Too many concurrent requests');
      }

      // Track active request
      this.activeRequests.set(request.method, activeCount + 1);

      try {
        // Check rate limit
        if (this.config.enableRateLimit && route.rateLimit) {
          if (!this.checkRateLimit(request.method, route.rateLimit)) {
            this.emit('rate-limit-exceeded', request.method, context);
            return this.createErrorResponse(request.id, -32000, 'Rate limit exceeded');
          }
        }

        // Check authentication (placeholder)
        if (this.config.enableAuth && route.requiresAuth) {
          // Implement auth check here
          // For now, just log
          console.log(`Auth required for method: ${request.method}`);
        }

        // Emit routing event
        this.emit('request-routed', request.method, context);

        // Execute handler
        const result = await Promise.race([
          route.handler(request, context),
          this.createTimeoutPromise(request.id),
        ]);

        // Update stats
        if (this.config.enableStats) {
          this.updateStats(request.method, Date.now() - startTime, true);
        }

        // Emit completion event
        this.emit('request-completed', request.method, context, Date.now() - startTime);

        return this.createSuccessResponse(request.id, result);

      } finally {
        // Decrement active request count
        const newCount = Math.max(0, (this.activeRequests.get(request.method) || 1) - 1);
        this.activeRequests.set(request.method, newCount);
      }

    } catch (error) {
      // Update stats
      if (this.config.enableStats) {
        this.updateStats(request.method, Date.now() - startTime, false);
      }

      // Emit error event
      this.emit('request-error', request.method, context, error as Error);

      // Return error response
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return this.createErrorResponse(request.id, -32603, `Internal error: ${errorMessage}`);
    }
  }

  /**
   * Get all registered routes
   */
  getRoutes(): RouteInfo[] {
    return Array.from(this.routes.values());
  }

  /**
   * Get route by method
   */
  getRoute(method: string): RouteInfo | null {
    return this.routes.get(method) || null;
  }

  /**
   * Check if route exists
   */
  hasRoute(method: string): boolean {
    return this.routes.has(method);
  }

  /**
   * Get request statistics
   */
  getStats(): RequestStats[] {
    return Array.from(this.stats.values());
  }

  /**
   * Get statistics for specific method
   */
  getMethodStats(method: string): RequestStats | null {
    return this.stats.get(method) || null;
  }

  /**
   * Get router status
   */
  getStatus(): {
    totalRoutes: number;
    activeRequests: number;
    rateLimitedMethods: string[];
    averageResponseTime: number;
  } {
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

  /**
   * Register built-in MCP routes
   */
  private registerBuiltinRoutes(): void {
    // Initialize route
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

    // Ping route
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

    // Tools list route
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

    // Tools call route
    this.registerRoute({
      method: 'tools/call',
      handler: async (request, context) => {
        if (!this.toolRegistry) {
          throw new Error('Tool registry not configured');
        }

        const { name, arguments: args } = request.params as {
          name: string;
          arguments: Record<string, unknown>;
        };

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

    // Completion route (placeholder)
    this.registerRoute({
      method: 'completion/complete',
      handler: async (_request) => {
        // Placeholder for completion functionality
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

  /**
   * Check rate limit for a method
   */
  private checkRateLimit(method: string, rateLimit: { requests: number; windowMs: number }): boolean {
    const now = Date.now();
    let state = this.rateLimits.get(method);

    if (!state || now > state.resetTime) {
      // Reset or initialize rate limit
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

    // Increment request count
    state.requests++;
    this.rateLimits.set(method, state);
    return true;
  }

  /**
   * Update request statistics
   */
  private updateStats(method: string, responseTime: number, success: boolean): void {
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

    // Update counters
    stats.totalRequests++;
    if (success) {
      stats.successfulRequests++;
    } else {
      stats.failedRequests++;
    }

    // Update average response time
    stats.averageResponseTime = (
      (stats.averageResponseTime * (stats.totalRequests - 1) + responseTime) / 
      stats.totalRequests
    );

    stats.lastRequestTime = new Date();
    this.stats.set(method, stats);
  }

  /**
   * Create timeout promise
   */
  private createTimeoutPromise(requestId: string | number): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Request ${requestId} timed out after ${this.config.requestTimeout}ms`));
      }, this.config.requestTimeout);
    });
  }

  /**
   * Create success response
   */
  private createSuccessResponse(id: string | number, result: unknown): JSONRPCResponse {
    return {
      jsonrpc: '2.0',
      id,
      result: result as any,
    };
  }

  /**
   * Create error response
   */
  private createErrorResponse(id: string | number, code: number, message: string): any {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code,
        message,
      },
    };
  }

  /**
   * Clear statistics
   */
  clearStats(): void {
    this.stats.clear();
    this.rateLimits.clear();
    this.activeRequests.clear();
  }

  /**
   * Get configuration
   */
  getConfig(): Readonly<RouterConfig> {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<RouterConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Typed event emitter methods
   */
  emit<K extends keyof RequestRouterEvents>(
    event: K,
    ...args: Parameters<RequestRouterEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }

  on<K extends keyof RequestRouterEvents>(
    event: K,
    listener: RequestRouterEvents[K]
  ): this {
    return super.on(event, listener);
  }

  off<K extends keyof RequestRouterEvents>(
    event: K,
    listener: RequestRouterEvents[K]
  ): this {
    return super.off(event, listener);
  }
}