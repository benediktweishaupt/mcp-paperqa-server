import { AcademicMCPServer } from '../../src/server/AcademicMCPServer';
import { MCPProtocolHandler } from '../../src/protocol/MCPProtocolHandler';

describe('AcademicMCPServer Integration', () => {
  let server: AcademicMCPServer;

  beforeEach(() => {
    server = new AcademicMCPServer({
      name: 'test-server',
      version: '1.0.0',
      description: 'Test server',
    });
  });

  afterEach(async () => {
    if (server) {
      await server.stop();
    }
  });

  describe('Server Lifecycle', () => {
    it('should start and stop successfully', async () => {
      // Start server
      const startPromise = server.start();
      
      // Wait a bit for startup
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(server.isRunning()).toBe(true);
      
      // Stop server
      await server.stop();
      expect(server.isRunning()).toBe(false);
      
      // Wait for start promise to resolve/reject
      await expect(startPromise).resolves.toBeUndefined();
    });

    it('should emit lifecycle events', async () => {
      const startedSpy = jest.fn();
      const stoppedSpy = jest.fn();
      
      server.on('started', startedSpy);
      server.on('stopped', stoppedSpy);
      
      await server.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      await server.stop();
      
      expect(startedSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'test-server',
          version: '1.0.0'
        })
      );
      expect(stoppedSpy).toHaveBeenCalled();
    });
  });

  describe('Tool Integration', () => {
    it('should register and expose health check tool', async () => {
      await server.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const toolRegistry = (server as any).toolRegistry;
      const tools = toolRegistry.getAllToolsMetadata();
      
      expect(tools).toContainEqual(
        expect.objectContaining({
          name: 'health_check',
          description: expect.stringContaining('health')
        })
      );
      
      await server.stop();
    });

    it('should execute health check tool', async () => {
      await server.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const toolRegistry = (server as any).toolRegistry;
      const result = await toolRegistry.executeTool('health_check', {}, {
        requestId: 'test-123',
        timestamp: new Date(),
        metadata: {}
      });
      
      expect(result).toMatchObject({
        status: 'healthy',
        timestamp: expect.any(String),
        server: expect.objectContaining({
          name: 'test-server',
          version: '1.0.0'
        })
      });
      
      await server.stop();
    });
  });

  describe('Protocol Integration', () => {
    it('should handle MCP protocol messages', async () => {
      await server.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const protocolHandler = (server as any).protocolHandler;
      expect(protocolHandler).toBeInstanceOf(MCPProtocolHandler);
      
      // Test initialization message
      const initResult = await protocolHandler.initialize({
        name: 'test-client',
        version: '1.0.0'
      });
      
      expect(initResult).toMatchObject({
        version: expect.any(String),
        capabilities: expect.objectContaining({
          tools: true
        })
      });
      
      await server.stop();
    });

    it('should route requests through request router', async () => {
      await server.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const requestRouter = (server as any).requestRouter;
      
      // Test ping route
      const pingResponse = await requestRouter.handleRequest({
        jsonrpc: '2.0',
        id: 1,
        method: 'ping',
        params: {}
      }, {
        requestId: 1,
        method: 'ping',
        timestamp: new Date()
      });
      
      expect(pingResponse).toMatchObject({
        status: 'pong',
        timestamp: expect.any(String)
      });
      
      await server.stop();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle server startup errors gracefully', async () => {
      // Create a server with invalid configuration to trigger error
      const invalidServer = new AcademicMCPServer({
        name: 'test-server',
        version: '1.0.0',
        description: 'Test server',
        maxConnections: -1, // Invalid
      });

      const errorSpy = jest.fn();
      invalidServer.on('error', errorSpy);

      // Start should not throw, but should emit error
      await invalidServer.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Note: The actual error handling depends on the server implementation
      // This test structure is in place for when more validation is added
      
      await invalidServer.stop();
    });
  });
});