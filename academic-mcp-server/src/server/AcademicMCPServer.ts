import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListToolsResult,
  JSONRPCMessage,
} from '@modelcontextprotocol/sdk/types.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { EventEmitter } from 'events';
import { ToolRegistry, ToolRegistryConfig, ToolContext } from '../tools';
import { healthCheckTool } from '../tools/builtins/HealthCheckTool';
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

/**
 * Academic MCP Server Class
 * Handles MCP protocol communication and tool management for academic research assistance
 */
export class AcademicMCPServer extends EventEmitter {
  private server: Server;
  private transport: StdioServerTransport | null = null;
  private state: ServerState;
  private options: AcademicMCPServerOptions;
  private shutdownHandlers: Array<() => Promise<void>> = [];
  private toolRegistry: ToolRegistry;
  private protocolHandler: MCPProtocolHandler;
  private streamHandler: MCPStreamHandler;
  private requestRouter: MCPRequestRouter;

  constructor(options: AcademicMCPServerOptions) {
    super();
    
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

    // Initialize Tool Registry
    this.toolRegistry = new ToolRegistry({
      enableValidation: true,
      enablePermissions: false,
      enableRateLimit: true,
      maxTools: 50,
      defaultCategory: 'academic',
      ...options.toolRegistry,
    });

    // Initialize Protocol Handler
    this.protocolHandler = new MCPProtocolHandler({
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

    // Initialize Stream Handler
    this.streamHandler = new MCPStreamHandler({
      chunkSize: 64 * 1024, // 64KB chunks
      maxConcurrentStreams: 5,
      streamTimeout: 300000, // 5 minutes
      compressionEnabled: false,
      enableProgress: true,
      ...options.streaming,
    });

    // Initialize Request Router
    this.requestRouter = new MCPRequestRouter({
      enableRateLimit: true,
      enableStats: true,
      enableAuth: false,
      requestTimeout: 30000,
      maxConcurrentRequests: this.options.maxConnections || 10,
      ...options.router,
    });

    // Connect router with tool registry
    this.requestRouter.setToolRegistry(this.toolRegistry);

    // Initialize MCP Server with capabilities
    this.server = new Server(
      {
        name: this.options.name,
        version: this.options.version,
        description: this.options.description,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupServerHandlers();
    this.setupEventHandlers();
    this.setupToolRegistry();
  }

  /**
   * Set up MCP server request handlers
   */
  private setupServerHandlers(): void {
    // Handle list_tools requests
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const toolsMetadata = this.toolRegistry.getAllToolsMetadata();
      const tools: ListToolsResult = {
        tools: toolsMetadata.map(metadata => ({
          name: metadata.name,
          description: metadata.description,
          inputSchema: metadata.inputSchema as any, // Convert to MCP schema format
        })),
      };
      
      this.emit('tools_listed', tools);
      return tools;
    });

    // Handle call_tool requests
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      this.emit('tool_called', { name, arguments: args });
      
      try {
        // Create tool context
        const context: ToolContext = {
          requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          metadata: {
            serverName: this.options.name,
            serverVersion: this.options.version,
          },
        };

        const result = await this.toolRegistry.executeTool(name, args || {}, context);
        return result;
      } catch (error) {
        this.emit('tool_error', { name, error, arguments: args });
        throw error;
      }
    });
  }

  /**
   * Set up internal event handlers
   * Note: Process event handlers are managed externally to avoid memory leaks in tests
   */
  private setupEventHandlers(): void {
    // Set up protocol handler events
    this.protocolHandler.on('connected', (connectionInfo) => {
      this.emit('protocol_connected', connectionInfo);
    });

    this.protocolHandler.on('disconnected', (reason) => {
      this.emit('protocol_disconnected', reason);
    });

    this.protocolHandler.on('error', (error) => {
      this.emit('protocol_error', error);
    });

    // Set up stream handler events
    this.streamHandler.on('chunk', (chunk) => {
      this.emit('stream_chunk', chunk);
    });

    this.streamHandler.on('completed', (streamId, totalChunks) => {
      this.emit('stream_completed', { streamId, totalChunks });
    });

    this.streamHandler.on('error', (error, streamId) => {
      this.emit('stream_error', { error, streamId });
    });

    // Set up request router events
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

  /**
   * Set up tool registry with built-in tools
   */
  private setupToolRegistry(): void {
    // Set up tool registry event handlers
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

    // Register built-in tools
    if (this.options.enableHealthCheck) {
      this.registerBuiltinTools();
    }
  }

  /**
   * Register built-in tools
   */
  private async registerBuiltinTools(): Promise<void> {
    try {
      await this.toolRegistry.registerTool(healthCheckTool);
    } catch (error) {
      console.error('Failed to register built-in tools:', error);
    }
  }

  /**
   * Start the MCP server
   */
  async start(): Promise<void> {
    if (this.state.isRunning) {
      throw new Error('Server is already running');
    }

    try {
      this.transport = new StdioServerTransport();
      await this.server.connect(this.transport);
      
      this.state.isRunning = true;
      this.state.startTime = new Date();
      
      this.emit('started', {
        name: this.options.name,
        version: this.options.version,
        startTime: this.state.startTime,
      });

      // Emit started event - logging handled by main application
      
    } catch (error) {
      this.emit('error', error);
      throw new Error(`Failed to start server: ${error}`);
    }
  }

  /**
   * Stop the MCP server gracefully
   */
  async stop(): Promise<void> {
    if (!this.state.isRunning) {
      return;
    }

    // Emit stopping event - logging handled by main application
    
    try {
      // Execute shutdown handlers
      for (const handler of this.shutdownHandlers) {
        await handler();
      }

      // Close server connection
      if (this.transport) {
        await this.server.close();
        this.transport = null;
      }

      this.state.isRunning = false;
      this.state.connections.clear();

      this.emit('stopped');
      // Emit stopped event - logging handled by main application
      
    } catch (error) {
      this.emit('error', error);
      throw new Error(`Error during server shutdown: ${error}`);
    }
  }

  /**
   * Register a shutdown handler
   */
  addShutdownHandler(handler: () => Promise<void>): void {
    this.shutdownHandlers.push(handler);
  }


  /**
   * Get current server state
   */
  getState(): Readonly<ServerState> {
    return { ...this.state };
  }

  /**
   * Get server options
   */
  getOptions(): Readonly<AcademicMCPServerOptions> {
    return { ...this.options };
  }

  /**
   * Check if server is running
   */
  isRunning(): boolean {
    return this.state.isRunning;
  }

  /**
   * Get server uptime in milliseconds
   */
  getUptime(): number {
    return Date.now() - this.state.startTime.getTime();
  }

  /**
   * Get the tool registry instance
   */
  getToolRegistry(): ToolRegistry {
    return this.toolRegistry;
  }

  /**
   * Register a new tool
   */
  async registerTool(registration: import('../tools').ToolRegistration): Promise<void> {
    await this.toolRegistry.registerTool(registration);
  }

  /**
   * Unregister a tool
   */
  async unregisterTool(name: string): Promise<boolean> {
    return this.toolRegistry.unregisterTool(name);
  }

  /**
   * Get all registered tools metadata
   */
  getRegisteredTools(): import('../tools').ToolMetadata[] {
    return this.toolRegistry.getAllToolsMetadata();
  }

  /**
   * Get tool registry statistics
   */
  getToolRegistryStats(): {
    totalTools: number;
    categoryCounts: Record<string, number>;
    deprecatedTools: string[];
    experimentalTools: string[];
  } {
    return this.toolRegistry.getStats();
  }

  /**
   * Get protocol handler
   */
  getProtocolHandler(): MCPProtocolHandler {
    return this.protocolHandler;
  }

  /**
   * Get stream handler
   */
  getStreamHandler(): MCPStreamHandler {
    return this.streamHandler;
  }

  /**
   * Get request router
   */
  getRequestRouter(): MCPRequestRouter {
    return this.requestRouter;
  }

  /**
   * Handle raw JSON-RPC message through protocol handler
   */
  async handleRawMessage(message: JSONRPCMessage): Promise<JSONRPCMessage | null> {
    try {
      const response = await this.protocolHandler.handleMessage(message);
      return response;
    } catch (error) {
      this.emit('protocol_error', error);
      throw error;
    }
  }

  /**
   * Get comprehensive server statistics
   */
  getServerStats() {
    return {
      server: this.getState(),
      tools: this.getToolRegistryStats(),
      protocol: this.protocolHandler.getStats(),
      router: this.requestRouter.getStatus(),
      streaming: this.streamHandler.getStreamStats(),
    };
  }

  /**
   * Process a large response through streaming
   */
  createResponseStream(data: unknown, metadata?: Record<string, unknown>): string {
    return this.streamHandler.createOutputStream(data, metadata);
  }

  /**
   * Initialize protocol connection
   */
  async initializeProtocol(clientInfo?: { name: string; version: string }): Promise<any> {
    return await this.protocolHandler.initialize(clientInfo);
  }
}