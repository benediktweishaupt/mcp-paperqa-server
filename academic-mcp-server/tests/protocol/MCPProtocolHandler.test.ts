import { MCPProtocolHandler } from '../../src/protocol/MCPProtocolHandler';
import { JSONRPCRequest, JSONRPCMessage } from '@modelcontextprotocol/sdk/types.js';

describe('MCPProtocolHandler', () => {
  let handler: MCPProtocolHandler;

  beforeEach(() => {
    handler = new MCPProtocolHandler({
      serverName: 'test-server',
      serverVersion: '1.0.0',
    });
  });

  afterEach(() => {
    handler.removeAllListeners();
  });

  describe('Constructor and Configuration', () => {
    test('should initialize with default configuration', () => {
      const config = handler.getConfig();
      expect(config.serverName).toBe('test-server');
      expect(config.serverVersion).toBe('1.0.0');
      expect(config.maxConcurrentRequests).toBe(10);
      expect(config.requestTimeout).toBe(30000);
    });

    test('should initialize with custom configuration', () => {
      const customHandler = new MCPProtocolHandler({
        serverName: 'custom-server',
        serverVersion: '2.0.0',
        maxConcurrentRequests: 5,
        requestTimeout: 15000,
      });

      const config = customHandler.getConfig();
      expect(config.serverName).toBe('custom-server');
      expect(config.serverVersion).toBe('2.0.0');
      expect(config.maxConcurrentRequests).toBe(5);
      expect(config.requestTimeout).toBe(15000);
    });

    test('should have initial connection state', () => {
      const state = handler.getConnectionState();
      expect(state.isConnected).toBe(false);
      expect(state.serverInfo.name).toBe('test-server');
      expect(state.serverInfo.version).toBe('1.0.0');
      expect(state.messagesSent).toBe(0);
      expect(state.messagesReceived).toBe(0);
    });
  });

  describe('Initialization', () => {
    test('should initialize connection successfully', async () => {
      const clientInfo = { name: 'test-client', version: '1.0.0' };
      const version = await handler.initialize(clientInfo);

      expect(version.version).toBe('1.0.0');
      expect(version.capabilities).toBeDefined();

      const state = handler.getConnectionState();
      expect(state.isConnected).toBe(true);
      expect(state.clientInfo).toEqual(clientInfo);
    });

    test('should emit connected event on initialization', async () => {
      const connectedSpy = jest.fn();
      handler.on('connected', connectedSpy);

      await handler.initialize({ name: 'test-client', version: '1.0.0' });

      expect(connectedSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          isConnected: true,
          clientInfo: { name: 'test-client', version: '1.0.0' },
        })
      );
    });
  });

  describe('Message Validation', () => {
    test('should validate correct JSON-RPC 2.0 request', async () => {
      const validRequest: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'ping',
      };

      const response = await handler.handleMessage(validRequest);
      expect(response).toBeDefined();
      expect(response!.jsonrpc).toBe('2.0');
      expect(response!.id).toBe(1);
    });

    test('should reject invalid JSON-RPC version', async () => {
      const invalidRequest = {
        jsonrpc: '1.0',
        id: 1,
        method: 'ping',
      } as any;

      const response = await handler.handleMessage(invalidRequest);
      expect(response).toBeDefined();
      expect(response!.error).toBeDefined();
      expect(response!.error!.code).toBe(-32600);
      expect(response!.error!.message).toContain('Invalid JSON-RPC version');
    });

    test('should reject message without method, result, or error', async () => {
      const invalidMessage = {
        jsonrpc: '2.0',
        id: 1,
      } as any;

      const response = await handler.handleMessage(invalidMessage);
      expect(response).toBeDefined();
      expect(response!.error).toBeDefined();
      expect(response!.error!.code).toBe(-32600);
    });

    test('should handle invalid method type', async () => {
      const invalidRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 123,
      } as any;

      const response = await handler.handleMessage(invalidRequest);
      expect(response).toBeDefined();
      expect(response!.error).toBeDefined();
      expect(response!.error!.message).toContain('Method must be a string');
    });
  });

  describe('Request Handling', () => {
    test('should handle initialize request', async () => {
      const initRequest: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          clientInfo: { name: 'test-client', version: '1.0.0' },
        },
      };

      const response = await handler.handleMessage(initRequest);
      expect(response).toBeDefined();
      expect(response!.result).toBeDefined();
      expect((response!.result as any).version).toBe('1.0.0');
      expect((response!.result as any).capabilities).toBeDefined();
    });

    test('should handle ping request', async () => {
      const pingRequest: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 2,
        method: 'ping',
      };

      const response = await handler.handleMessage(pingRequest);
      expect(response).toBeDefined();
      expect(response!.result).toEqual({ status: 'pong' });
    });

    test('should reject unsupported method', async () => {
      const unsupportedRequest: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 3,
        method: 'unsupported_method',
      };

      const response = await handler.handleMessage(unsupportedRequest);
      expect(response).toBeDefined();
      expect(response!.error).toBeDefined();
      expect(response!.error!.code).toBe(-32601);
      expect(response!.error!.message).toContain('Method \'unsupported_method\' not found');
    });

    test('should handle tools/list method delegation', async () => {
      const toolsRequest: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 4,
        method: 'tools/list',
      };

      const response = await handler.handleMessage(toolsRequest);
      expect(response).toBeDefined();
      expect(response!.error).toBeDefined();
      expect(response!.error!.message).toContain('should be handled by server');
    });
  });

  describe('Notification Handling', () => {
    test('should handle notifications without response', async () => {
      const notification: JSONRPCMessage = {
        jsonrpc: '2.0',
        method: 'notifications/cancelled',
        params: { requestId: 1 },
      };

      const response = await handler.handleMessage(notification);
      expect(response).toBeNull();
    });

    test('should emit notification event', async () => {
      const notificationSpy = jest.fn();
      handler.on('notification', notificationSpy);

      const notification: JSONRPCMessage = {
        jsonrpc: '2.0',
        method: 'notifications/progress',
        params: { progress: 50 },
      };

      await handler.handleMessage(notification);
      expect(notificationSpy).toHaveBeenCalledWith(notification);
    });
  });

  describe('Event Emission', () => {
    test('should emit message-received event', async () => {
      const messageReceivedSpy = jest.fn();
      handler.on('message-received', messageReceivedSpy);

      const request: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'ping',
      };

      await handler.handleMessage(request);
      expect(messageReceivedSpy).toHaveBeenCalledWith(request);
    });

    test('should emit request event for requests', async () => {
      const requestSpy = jest.fn();
      handler.on('request', requestSpy);

      const request: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'ping',
      };

      await handler.handleMessage(request);
      expect(requestSpy).toHaveBeenCalledWith(request);
    });

    test('should emit error event on handler error', async () => {
      const errorSpy = jest.fn();
      handler.on('error', errorSpy);

      // Mock an error by overriding handleRequest
      const originalHandleRequest = (handler as any).handleRequest;
      (handler as any).handleRequest = jest.fn().mockRejectedValue(new Error('Test error'));

      const request: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'ping',
      };

      await handler.handleMessage(request);
      expect(errorSpy).toHaveBeenCalled();

      // Restore original method
      (handler as any).handleRequest = originalHandleRequest;
    });
  });

  describe('Connection State Management', () => {
    test('should update message counters', async () => {
      const initialState = handler.getConnectionState();
      expect(initialState.messagesReceived).toBe(0);

      const request: JSONRPCRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'ping',
      };

      await handler.handleMessage(request);

      const updatedState = handler.getConnectionState();
      expect(updatedState.messagesReceived).toBe(1);
      expect(updatedState.lastActivity).toBeInstanceOf(Date);
    });

    test('should disconnect properly', async () => {
      const disconnectedSpy = jest.fn();
      handler.on('disconnected', disconnectedSpy);

      await handler.initialize({ name: 'test-client', version: '1.0.0' });
      expect(handler.getConnectionState().isConnected).toBe(true);

      await handler.disconnect('Test disconnect');
      expect(handler.getConnectionState().isConnected).toBe(false);
      expect(disconnectedSpy).toHaveBeenCalledWith('Test disconnect');
    });
  });

  describe('Statistics', () => {
    test('should provide protocol statistics', () => {
      const stats = handler.getStats();
      expect(stats).toHaveProperty('messagesSent');
      expect(stats).toHaveProperty('messagesReceived');
      expect(stats).toHaveProperty('activeRequests');
      expect(stats).toHaveProperty('isConnected');
      expect(stats).toHaveProperty('uptime');
      expect(typeof stats.uptime).toBe('number');
    });
  });

  describe('Configuration Updates', () => {
    test('should update configuration', () => {
      const originalConfig = handler.getConfig();
      expect(originalConfig.requestTimeout).toBe(30000);

      handler.updateConfig({ requestTimeout: 60000 });

      const updatedConfig = handler.getConfig();
      expect(updatedConfig.requestTimeout).toBe(60000);
      expect(updatedConfig.serverName).toBe('test-server'); // Should preserve other values
    });
  });
});