import { EventEmitter } from 'events';
import { 
  JSONRPCMessage, 
  JSONRPCRequest, 
  JSONRPCResponse
} from '@modelcontextprotocol/sdk/types.js';

/**
 * MCP Protocol Version Information
 */
export interface MCPVersion {
  version: string;
  capabilities?: {
    tools?: boolean;
    resources?: boolean;
    prompts?: boolean;
    roots?: boolean;
  } | undefined;
}

/**
 * MCP Connection State
 */
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

/**
 * MCP Protocol Events
 */
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

/**
 * Request Context for MCP operations
 */
export interface MCPRequestContext {
  requestId: string | number | null;
  method: string;
  timestamp: Date;
  clientId?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Message Queue Entry
 */
interface QueuedMessage {
  id: string;
  message: JSONRPCMessage;
  timestamp: Date;
  retryCount: number;
  context?: MCPRequestContext;
}

/**
 * MCP Protocol Handler Configuration
 */
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

/**
 * MCP Protocol Handler
 * Handles JSON-RPC 2.0 communication for MCP protocol
 */
export class MCPProtocolHandler extends EventEmitter {
  private config: MCPProtocolConfig;
  private connectionState: MCPConnectionState;
  private messageQueue = new Map<string, QueuedMessage>();
  private activeRequests = new Map<string | number, NodeJS.Timeout>();
  private requestIdCounter = 0;

  constructor(config: Partial<MCPProtocolConfig> = {}) {
    super();
    
    this.config = {
      serverName: 'academic-mcp-server',
      serverVersion: '1.0.0',
      maxConcurrentRequests: 10,
      requestTimeout: 30000, // 30 seconds
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

  /**
   * Initialize MCP connection
   */
  async initialize(clientInfo?: { name: string; version: string }): Promise<MCPVersion> {
    this.connectionState.isConnected = true;
    this.connectionState.clientInfo = clientInfo as { name: string; version: string } | undefined;
    this.connectionState.version = {
      version: this.config.serverVersion,
      capabilities: this.config.capabilities as MCPVersion['capabilities'],
    };
    this.connectionState.lastActivity = new Date();

    this.emit('connected', this.connectionState);

    return {
      version: this.config.serverVersion,
      capabilities: this.config.capabilities as MCPVersion['capabilities'],
    };
  }

  /**
   * Handle incoming JSON-RPC message
   */
  async handleMessage(message: JSONRPCMessage): Promise<any | null> {
    this.connectionState.messagesReceived++;
    this.connectionState.lastActivity = new Date();
    this.emit('message-received', message);

    try {
      // Validate message format
      const validationResult = this.validateMessage(message);
      if (!validationResult.valid) {
        if ('id' in message && message.id !== undefined) {
          return this.createErrorResponse(message.id, -32600, validationResult.error || 'Invalid Request');
        }
        return null; // Invalid notification
      }

      // Handle different message types
      if (this.isRequest(message)) {
        this.emit('request', message);
        return await this.handleRequest(message);
      } else if (this.isResponse(message)) {
        this.emit('response', message as JSONRPCResponse);
        this.handleResponse(message as JSONRPCResponse);
        return null;
      } else if (this.isNotification(message)) {
        this.emit('notification', message);
        await this.handleNotification(message);
        return null;
      }

      // Unknown message type
      if ('id' in message && message.id !== undefined) {
        return this.createErrorResponse(message.id, -32600, 'Invalid Request');
      }
      return null;

    } catch (error) {
      this.emit('error', error as Error);
      if ('id' in message && message.id !== undefined) {
        return this.createErrorResponse(message.id, -32603, 'Internal error');
      }
      return null;
    }
  }

  /**
   * Send a JSON-RPC request
   */
  async sendRequest(
    method: string, 
    params?: unknown, 
    timeout?: number
  ): Promise<any> {
    const id = ++this.requestIdCounter;
    const request: JSONRPCRequest = {
      jsonrpc: '2.0',
      id,
      method,
      params: params as any,
    };

    return new Promise((resolve, reject) => {
      // Set up timeout
      const timeoutMs = timeout || this.config.requestTimeout;
      const timeoutHandle = setTimeout(() => {
        this.activeRequests.delete(id);
        reject(new Error(`Request timeout after ${timeoutMs}ms`));
      }, timeoutMs);

      this.activeRequests.set(id, timeoutHandle);

      // Send message
      this.sendMessage(request);

      // Store resolver for response handling
      const originalResolver = resolve;
      this.activeRequests.set(id, {
        ...timeoutHandle,
        resolve: originalResolver,
        reject,
      } as any);
    });
  }

  /**
   * Send a JSON-RPC notification
   */
  sendNotification(method: string, params?: unknown): void {
    const notification: JSONRPCMessage = {
      jsonrpc: '2.0',
      method,
      params: params as any,
    };

    this.sendMessage(notification);
  }

  /**
   * Send a JSON-RPC response
   */
  sendResponse(id: string | number, result?: unknown, error?: any): void {
    const response: any = {
      jsonrpc: '2.0',
      id,
    };

    if (error) {
      response.error = error;
    } else {
      response.result = result as any;
    }

    this.sendMessage(response);
  }

  /**
   * Send message (to be overridden by transport layer)
   */
  protected sendMessage(message: JSONRPCMessage): void {
    this.connectionState.messagesSent++;
    this.connectionState.lastActivity = new Date();
    this.emit('message-sent', message);
    
    // This method should be overridden by transport implementations
    // For now, just emit the message for testing
    console.log('Sending message:', JSON.stringify(message, null, 2));
  }

  /**
   * Handle JSON-RPC request
   */
  private async handleRequest(request: JSONRPCRequest): Promise<any> {
    // Request context for future use
    // const _context: MCPRequestContext = {
    //   requestId: request.id,
    //   method: request.method,
    //   timestamp: new Date(),
    // };

    try {
      // Check if method is supported
      if (!this.config.supportedMethods.includes(request.method)) {
        return this.createErrorResponse(request.id, -32601, `Method '${request.method}' not found`);
      }

      // Handle built-in methods
      switch (request.method) {
        case 'initialize':
          const initResult = await this.handleInitialize(request.params);
          return this.createSuccessResponse(request.id, initResult);

        case 'ping':
          return this.createSuccessResponse(request.id, { status: 'pong' });

        case 'tools/list':
          // This will be handled by the server implementation
          return this.createErrorResponse(request.id, -32601, 'Method should be handled by server');

        case 'tools/call':
          // This will be handled by the server implementation
          return this.createErrorResponse(request.id, -32601, 'Method should be handled by server');

        default:
          return this.createErrorResponse(request.id, -32601, `Unknown method: ${request.method}`);
      }

    } catch (error) {
      return this.createErrorResponse(request.id, -32603, `Internal error: ${(error as Error).message}`);
    }
  }

  /**
   * Handle JSON-RPC response
   */
  private handleResponse(response: any): void {
    const requestInfo = this.activeRequests.get(response.id);
    if (requestInfo) {
      this.activeRequests.delete(response.id);
      
      // Clear timeout
      if (typeof requestInfo === 'object' && 'resolve' in requestInfo) {
        clearTimeout(requestInfo as NodeJS.Timeout);
        
        if (response.error) {
          (requestInfo as any).reject(new Error(response.error.message));
        } else {
          (requestInfo as any).resolve(response);
        }
      }
    }
  }

  /**
   * Handle JSON-RPC notification
   */
  private async handleNotification(notification: any): Promise<void> {
    // Handle notifications (fire-and-forget messages)
    switch ((notification as any).method) {
      case 'notifications/cancelled':
        // Handle request cancellation
        break;
      case 'notifications/progress':
        // Handle progress updates
        break;
      default:
        console.log(`Unhandled notification: ${(notification as any).method}`);
    }
  }

  /**
   * Handle initialize request
   */
  private async handleInitialize(params: unknown): Promise<any> {
    const clientInfo = params as { clientInfo?: { name: string; version: string } };
    
    if (clientInfo?.clientInfo) {
      this.connectionState.clientInfo = clientInfo.clientInfo;
    }

    return {
      version: this.config.serverVersion,
      capabilities: this.config.capabilities || {},
    };
  }

  /**
   * Validate JSON-RPC message format
   */
  private validateMessage(message: any): { valid: boolean; error?: string } {
    if (!message || typeof message !== 'object') {
      return { valid: false, error: 'Message must be an object' };
    }

    if (message.jsonrpc !== '2.0') {
      return { valid: false, error: 'Invalid JSON-RPC version' };
    }

    if (!message.method && !('result' in message) && !('error' in message)) {
      return { valid: false, error: 'Message must have method, result, or error' };
    }

    // Additional validation for specific message types
    if (message.method && typeof message.method !== 'string') {
      return { valid: false, error: 'Method must be a string' };
    }

    if ('id' in message && message.id !== null && typeof message.id !== 'string' && typeof message.id !== 'number') {
      return { valid: false, error: 'ID must be string, number, or null' };
    }

    return { valid: true };
  }

  /**
   * Check if message is a request
   */
  private isRequest(message: JSONRPCMessage): message is JSONRPCRequest {
    return 'method' in message && 'id' in message && message.id !== undefined;
  }

  /**
   * Check if message is a response
   */
  private isResponse(message: any): boolean {
    return 'id' in message && ('result' in message || 'error' in message);
  }

  /**
   * Check if message is a notification
   */
  private isNotification(message: any): boolean {
    return 'method' in message && !('id' in message);
  }

  /**
   * Create success response
   */
  private createSuccessResponse(id: string | number, result: unknown): any {
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
   * Get connection state
   */
  getConnectionState(): Readonly<MCPConnectionState> {
    return { ...this.connectionState };
  }

  /**
   * Get protocol configuration
   */
  getConfig(): Readonly<MCPProtocolConfig> {
    return { ...this.config };
  }

  /**
   * Update protocol configuration
   */
  updateConfig(newConfig: Partial<MCPProtocolConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Disconnect and cleanup
   */
  async disconnect(reason?: string): Promise<void> {
    this.connectionState.isConnected = false;
    
    // Clear active requests
    for (const [_id, requestInfo] of this.activeRequests.entries()) {
      if (typeof requestInfo === 'object' && 'reject' in requestInfo) {
        clearTimeout(requestInfo as NodeJS.Timeout);
        (requestInfo as any).reject(new Error('Connection closed'));
      }
    }
    this.activeRequests.clear();

    // Clear message queue
    this.messageQueue.clear();

    this.emit('disconnected', reason);
  }

  /**
   * Get protocol statistics
   */
  getStats(): {
    messagesSent: number;
    messagesReceived: number;
    activeRequests: number;
    queuedMessages: number;
    isConnected: boolean;
    uptime: number;
  } {
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

  /**
   * Typed event emitter methods
   */
  emit<K extends keyof MCPProtocolEvents>(
    event: K,
    ...args: Parameters<MCPProtocolEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }

  on<K extends keyof MCPProtocolEvents>(
    event: K,
    listener: MCPProtocolEvents[K]
  ): this {
    return super.on(event, listener);
  }

  off<K extends keyof MCPProtocolEvents>(
    event: K,
    listener: MCPProtocolEvents[K]
  ): this {
    return super.off(event, listener);
  }
}