import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  CallToolResult,
  ListToolsResult,
} from '@modelcontextprotocol/sdk/types.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { EventEmitter } from 'events';

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
  }

  /**
   * Set up MCP server request handlers
   */
  private setupServerHandlers(): void {
    // Handle list_tools requests
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools: ListToolsResult = {
        tools: [
          // Placeholder - tools will be added in subsequent tasks
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

    // Handle call_tool requests
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      this.emit('tool_called', { name, arguments: args });
      
      try {
        const result = await this.handleToolCall(name, args || {});
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
    // Event handlers will be set up in the main application
    // This prevents memory leaks during testing where multiple instances are created
  }

  /**
   * Handle tool call requests
   */
  private async handleToolCall(name: string, _args: Record<string, unknown>): Promise<CallToolResult> {
    switch (name) {
      case 'health_check':
        return this.handleHealthCheck();
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  /**
   * Handle health check tool call
   */
  private handleHealthCheck(): CallToolResult {
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
}