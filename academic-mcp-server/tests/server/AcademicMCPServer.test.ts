import { AcademicMCPServer } from '../../src/server/AcademicMCPServer';

describe('AcademicMCPServer', () => {
  let server: AcademicMCPServer;

  beforeEach(() => {
    server = new AcademicMCPServer({
      name: 'test-server',
      version: '1.0.0',
      description: 'Test server',
      enableHealthCheck: true,
      maxConnections: 5,
    });
  });

  afterEach(async () => {
    if (server.isRunning()) {
      await server.stop();
    }
  });

  describe('Construction', () => {
    test('should create server with correct options', () => {
      const options = server.getOptions();
      expect(options.name).toBe('test-server');
      expect(options.version).toBe('1.0.0');
      expect(options.description).toBe('Test server');
      expect(options.enableHealthCheck).toBe(true);
      expect(options.maxConnections).toBe(5);
    });

    test('should initialize with default options', () => {
      const defaultServer = new AcademicMCPServer({
        name: 'default',
        version: '1.0.0',
      });
      
      const options = defaultServer.getOptions();
      expect(options.enableHealthCheck).toBe(true);
      expect(options.maxConnections).toBe(10);
    });

    test('should have initial state', () => {
      const state = server.getState();
      expect(state.isRunning).toBe(false);
      expect(state.connections.size).toBe(0);
      expect(state.registeredTools.size).toBe(1); // health_check tool is registered by default
      expect(state.startTime).toBeInstanceOf(Date);
    });
  });

  describe('Server State', () => {
    test('should return running status correctly', () => {
      expect(server.isRunning()).toBe(false);
    });

    test('should calculate uptime', () => {
      const uptime = server.getUptime();
      expect(typeof uptime).toBe('number');
      expect(uptime).toBeGreaterThanOrEqual(0);
    });

    test('should provide immutable state', () => {
      const state1 = server.getState();
      const state2 = server.getState();
      
      expect(state1).not.toBe(state2); // Different objects
      expect(state1).toEqual(state2); // Same content
    });
  });

  describe('Event Handling', () => {
    test('should be an event emitter', () => {
      expect(server.on).toBeDefined();
      expect(server.emit).toBeDefined();
      expect(server.removeListener).toBeDefined();
    });

    test('should emit events', (done) => {
      server.on('test-event', (data) => {
        expect(data.message).toBe('test');
        done();
      });
      
      server.emit('test-event', { message: 'test' });
    });
  });

  describe('Shutdown Handlers', () => {
    test('should accept shutdown handlers', () => {
      const handler = jest.fn(async () => {});
      expect(() => server.addShutdownHandler(handler)).not.toThrow();
    });

    test('should accept multiple shutdown handlers', () => {
      const handler1 = jest.fn(async () => {});
      const handler2 = jest.fn(async () => {});
      
      expect(() => {
        server.addShutdownHandler(handler1);
        server.addShutdownHandler(handler2);
      }).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    test('should handle double start attempts', async () => {
      // Mock the server to simulate running state
      (server as any).state.isRunning = true;
      
      await expect(server.start()).rejects.toThrow('Server is already running');
    });

    test('should handle stop when not running', async () => {
      // Should not throw
      await expect(server.stop()).resolves.toBeUndefined();
    });
  });

  describe('Options Validation', () => {
    test('should accept minimal options', () => {
      expect(() => {
        new AcademicMCPServer({
          name: 'minimal',
          version: '1.0.0',
        });
      }).not.toThrow();
    });

    test('should accept full options', () => {
      expect(() => {
        new AcademicMCPServer({
          name: 'full',
          version: '1.0.0',
          description: 'Full test',
          enableHealthCheck: false,
          maxConnections: 20,
        });
      }).not.toThrow();
    });
  });
});