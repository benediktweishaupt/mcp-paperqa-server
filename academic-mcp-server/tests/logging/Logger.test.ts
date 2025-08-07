import { MCPLogger } from '../../src/logging/Logger';
import { ToolError } from '../../src/errors/MCPErrors';

// Mock winston to avoid actual file operations in tests
jest.mock('winston', () => {
  const mockLogger = {
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn(),
    level: 'info',
    transports: [],
    close: jest.fn(),
  };

  return {
    createLogger: jest.fn(() => mockLogger),
    transports: {
      Console: jest.fn(),
      File: jest.fn(),
    },
    format: {
      combine: jest.fn((...args) => args),
      colorize: jest.fn(),
      timestamp: jest.fn(),
      printf: jest.fn((fn) => ({ formatter: fn })),
      simple: jest.fn(),
    },
  };
});

describe('MCPLogger', () => {
  let logger: MCPLogger;
  let mockWinstonLogger: any;

  beforeEach(() => {
    logger = new MCPLogger({
      level: 'debug',
      enableConsole: true,
      enableFile: false,
    });
    
    // Access the mocked winston logger
    const winston = require('winston');
    mockWinstonLogger = winston.createLogger();
    jest.clearAllMocks();
  });

  afterEach(() => {
    logger.cleanup();
  });

  describe('Construction and Configuration', () => {
    test('should create logger with default configuration', () => {
      const defaultLogger = new MCPLogger();
      const config = defaultLogger.getConfig();
      
      expect(config.level).toBe('info');
      expect(config.enableConsole).toBe(true);
      expect(config.enableFile).toBe(false);
      expect(config.enableStructuredLogging).toBe(true);
      expect(config.enablePerformanceLogging).toBe(true);
      expect(config.sensitiveFields).toContain('password');
      
      defaultLogger.cleanup();
    });

    test('should create logger with custom configuration', () => {
      const customLogger = new MCPLogger({
        level: 'error',
        enableConsole: false,
        enableFile: true,
        enableStructuredLogging: false,
        sensitiveFields: ['custom-secret'],
      });

      const config = customLogger.getConfig();
      expect(config.level).toBe('error');
      expect(config.enableConsole).toBe(false);
      expect(config.enableFile).toBe(true);
      expect(config.enableStructuredLogging).toBe(false);
      expect(config.sensitiveFields).toContain('custom-secret');
      
      customLogger.cleanup();
    });
  });

  describe('Basic Logging Methods', () => {
    test('should log error messages', () => {
      const testError = new Error('Test error');
      logger.error('Error occurred', testError, { correlationId: 'test-123' });

      expect(mockWinstonLogger.error).toHaveBeenCalledWith({
        message: 'Error occurred',
        correlationId: 'test-123',
        error: {
          name: 'Error',
          message: 'Test error',
          stack: expect.any(String),
        },
      });
    });

    test('should log MCP errors with proper format', () => {
      const mcpError = new ToolError('Tool failed', 'test-tool', 'execute', true, 'corr-123');
      logger.error('MCP error occurred', mcpError);

      expect(mockWinstonLogger.error).toHaveBeenCalledWith({
        message: 'MCP error occurred',
        error: expect.objectContaining({
          name: 'ToolError',
          message: 'Tool failed',
          code: -32001,
          correlationId: 'corr-123',
        }),
      });
    });

    test('should log warning messages', () => {
      logger.warn('Warning message', { operation: 'test-op' });

      expect(mockWinstonLogger.warn).toHaveBeenCalledWith({
        message: 'Warning message',
        operation: 'test-op',
      });
    });

    test('should log info messages', () => {
      logger.info('Info message', { requestId: 'req-456' });

      expect(mockWinstonLogger.info).toHaveBeenCalledWith({
        message: 'Info message',
        requestId: 'req-456',
      });
    });

    test('should log debug messages', () => {
      logger.debug('Debug message', { metadata: { detail: 'test' } });

      expect(mockWinstonLogger.debug).toHaveBeenCalledWith({
        message: 'Debug message',
        metadata: { detail: 'test' },
      });
    });
  });

  describe('Correlation ID Generation', () => {
    test('should generate unique correlation IDs', () => {
      const id1 = logger.generateCorrelationId();
      const id2 = logger.generateCorrelationId();

      expect(id1).toMatch(/^mcp-[a-f0-9-]{36}$/);
      expect(id2).toMatch(/^mcp-[a-f0-9-]{36}$/);
      expect(id1).not.toBe(id2);
    });
  });

  describe('Request Logging', () => {
    test('should log request start', () => {
      logger.logRequestStart('tools/call', 'corr-123', { toolName: 'test-tool' });

      expect(mockWinstonLogger.info).toHaveBeenCalledWith({
        message: 'Request started',
        correlationId: 'corr-123',
        method: 'tools/call',
        operation: 'request_start',
        metadata: { params: { toolName: 'test-tool' } },
      });
    });

    test('should log successful request completion', () => {
      logger.logRequestEnd('tools/call', 'corr-123', true, 150, { result: 'success' });

      expect(mockWinstonLogger.info).toHaveBeenCalledWith(
        'Request completed successfully',
        expect.objectContaining({
          correlationId: 'corr-123',
          method: 'tools/call',
          operation: 'request_end',
          duration: 150,
          metadata: expect.objectContaining({
            success: true,
            result: { result: 'success' },
          }),
        })
      );
    });

    test('should log failed request completion', () => {
      const error = new Error('Request failed');
      logger.logRequestEnd('tools/call', 'corr-123', false, 300, undefined, error);

      expect(mockWinstonLogger.error).toHaveBeenCalledWith(
        'Request failed',
        error,
        expect.objectContaining({
          correlationId: 'corr-123',
          method: 'tools/call',
          operation: 'request_end',
          duration: 300,
          metadata: expect.objectContaining({
            success: false,
          }),
        })
      );
    });
  });

  describe('Performance Tracking', () => {
    test('should track performance with valid tracking ID', () => {
      const trackingId = logger.startPerformanceTracking('database-query', { correlationId: 'corr-123' });

      expect(trackingId).toBeDefined();
      expect(typeof trackingId).toBe('string');
      expect(mockWinstonLogger.debug).toHaveBeenCalledWith(
        'Performance tracking started',
        expect.objectContaining({
          correlationId: 'corr-123',
          operation: 'database-query',
          trackingId,
        })
      );
    });

    test('should end performance tracking with metrics', async () => {
      const trackingId = logger.startPerformanceTracking('api-call');
      
      // Small delay to ensure measurable duration
      await new Promise(resolve => setTimeout(resolve, 10));
      
      const metrics = logger.endPerformanceTracking(trackingId, true, undefined, { customMetric: 'value' });

      expect(metrics).toBeDefined();
      expect(metrics!.operation).toBe('api-call');
      expect(metrics!.duration).toBeGreaterThan(0);
      expect(metrics!.success).toBe(true);
      expect(metrics!.memoryUsage).toBeDefined();

      expect(mockWinstonLogger.info).toHaveBeenCalledWith(
        expect.stringMatching(/Performance: api-call completed in \d+ms/),
        expect.objectContaining({
          operation: 'performance_metrics',
          metadata: expect.objectContaining({
            customMetric: 'value',
            metrics: expect.objectContaining({
              operation: 'api-call',
              success: true,
            }),
          }),
        })
      );
    });

    test('should handle invalid tracking ID gracefully', () => {
      const metrics = logger.endPerformanceTracking('invalid-id');

      expect(metrics).toBeNull();
      expect(mockWinstonLogger.warn).toHaveBeenCalledWith(
        'Performance tracking not found',
        { trackingId: 'invalid-id' }
      );
    });
  });

  describe('Tool Execution Logging', () => {
    test('should log successful tool execution', () => {
      logger.logToolExecution(
        'search-tool',
        'execute',
        true,
        200,
        'corr-123',
        undefined,
        { query: 'test' }
      );

      expect(mockWinstonLogger.info).toHaveBeenCalledWith(
        'Tool execution: search-tool.execute completed',
        expect.objectContaining({
          correlationId: 'corr-123',
          toolName: 'search-tool',
          operation: 'execute',
          duration: 200,
          metadata: expect.objectContaining({
            success: true,
            arguments: { query: 'test' },
          }),
        })
      );
    });

    test('should log failed tool execution', () => {
      const error = new Error('Tool failed');
      logger.logToolExecution('search-tool', 'execute', false, 100, 'corr-123', error);

      expect(mockWinstonLogger.error).toHaveBeenCalledWith(
        'Tool execution: search-tool.execute failed',
        error,
        expect.objectContaining({
          correlationId: 'corr-123',
          toolName: 'search-tool',
          operation: 'execute',
          duration: 100,
          metadata: expect.objectContaining({
            success: false,
          }),
        })
      );
    });
  });

  describe('Child Logger', () => {
    test('should create child logger with default context', () => {
      const childLogger = logger.child({ correlationId: 'child-123', operation: 'child-op' });

      childLogger.info('Child log message');

      expect(mockWinstonLogger.info).toHaveBeenCalledWith({
        message: 'Child log message',
        correlationId: 'child-123',
        operation: 'child-op',
      });

      childLogger.cleanup();
    });

    test('should merge child context with additional context', () => {
      const childLogger = logger.child({ correlationId: 'child-123' });

      childLogger.error('Error message', new Error('Test'), { requestId: 'req-456' });

      expect(mockWinstonLogger.error).toHaveBeenCalledWith({
        message: 'Error message',
        correlationId: 'child-123',
        requestId: 'req-456',
        error: expect.objectContaining({
          name: 'Error',
          message: 'Test',
        }),
      });

      childLogger.cleanup();
    });
  });

  describe('Configuration Management', () => {
    test('should set log level dynamically', () => {
      logger.setLogLevel('error');

      expect(mockWinstonLogger.level).toBe('error');
    });

    test('should provide statistics', () => {
      // Start some performance tracking to test stats
      logger.startPerformanceTracking('test-op-1');
      logger.startPerformanceTracking('test-op-2');

      const stats = logger.getStats();

      expect(stats.activePerformanceTracking).toBe(2);
      expect(stats.logLevel).toBeDefined();
      expect(stats.transportsCount).toBeDefined();
    });
  });

  describe('Sensitive Data Sanitization', () => {
    test('should redact sensitive fields in logs', () => {
      const sensitiveData = {
        username: 'testuser',
        password: 'secret123',
        token: 'bearer-token',
        normalField: 'normal-value',
      };

      logger.info('Login attempt', { metadata: sensitiveData });

      expect(mockWinstonLogger.info).toHaveBeenCalledWith({
        message: 'Login attempt',
        metadata: {
          username: 'testuser',
          password: '[REDACTED]',
          token: '[REDACTED]',
          normalField: 'normal-value',
        },
      });
    });

    test('should recursively sanitize nested objects', () => {
      const nestedData = {
        user: {
          id: 123,
          credentials: {
            password: 'secret',
            apiKey: 'key123',
          },
        },
        request: {
          headers: {
            authorization: 'Bearer token123',
          },
        },
      };

      logger.info('Complex object', { metadata: nestedData });

      const logCall = mockWinstonLogger.info.mock.calls[0][0];
      expect(logCall.metadata.user.credentials.password).toBe('[REDACTED]');
      expect(logCall.metadata.request.headers.authorization).toBe('[REDACTED]');
      expect(logCall.metadata.user.id).toBe(123);
    });
  });
});