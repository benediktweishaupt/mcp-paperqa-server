import {
  MCPError,
  ProtocolError,
  ValidationError,
  ToolError,
  NotFoundError,
  RateLimitError,
  TimeoutError,
  MCPErrorFactory,
  ErrorCodes,
  isMCPError,
  isRecoverableError,
} from '../../src/errors/MCPErrors';

describe('MCPErrors', () => {
  describe('MCPError Base Class', () => {
    class TestMCPError extends MCPError {
      constructor(message: string, recoverable = false) {
        super(message, -32000, recoverable, 'test-correlation-id', { testContext: true });
      }
    }

    test('should create base error with all properties', () => {
      const error = new TestMCPError('Test error message', true);

      expect(error.message).toBe('Test error message');
      expect(error.code).toBe(-32000);
      expect(error.recoverable).toBe(true);
      expect(error.correlationId).toBe('test-correlation-id');
      expect(error.context).toEqual({ testContext: true });
      expect(error.timestamp).toBeInstanceOf(Date);
      expect(error.name).toBe('TestMCPError');
    });

    test('should convert to JSON-RPC format', () => {
      const error = new TestMCPError('Test error');
      const jsonrpc = error.toJSONRPC();

      expect(jsonrpc.code).toBe(-32000);
      expect(jsonrpc.message).toBe('Test error');
      expect(jsonrpc.data).toBeDefined();
      expect(jsonrpc.data?.timestamp).toBeDefined();
      expect(jsonrpc.data?.correlationId).toBe('test-correlation-id');
      expect(jsonrpc.data?.recoverable).toBe(false);
    });

    test('should convert to log format', () => {
      const error = new TestMCPError('Test error');
      const logFormat = error.toLogFormat();

      expect(logFormat.name).toBe('TestMCPError');
      expect(logFormat.message).toBe('Test error');
      expect(logFormat.code).toBe(-32000);
      expect(logFormat.timestamp).toBeDefined();
      expect(logFormat.correlationId).toBe('test-correlation-id');
    });
  });

  describe('Specific Error Types', () => {
    test('ProtocolError should have correct defaults', () => {
      const error = new ProtocolError('Invalid protocol', -32600, 'corr-123');

      expect(error.code).toBe(-32600);
      expect(error.recoverable).toBe(false);
      expect(error.correlationId).toBe('corr-123');
    });

    test('ValidationError should include field information', () => {
      const error = new ValidationError('Invalid field', 'username', 'invalid-value');

      expect(error.code).toBe(-32602);
      expect(error.field).toBe('username');
      expect(error.value).toBe('invalid-value');
      expect(error.recoverable).toBe(false);

      const jsonrpc = error.toJSONRPC();
      expect(jsonrpc.data?.field).toBe('username');
      expect(jsonrpc.data?.value).toBe('invalid-value');
    });

    test('ToolError should include tool information', () => {
      const error = new ToolError('Tool failed', 'test-tool', 'execute', true, 'corr-123');

      expect(error.code).toBe(-32001);
      expect(error.toolName).toBe('test-tool');
      expect(error.operation).toBe('execute');
      expect(error.recoverable).toBe(true);

      const jsonrpc = error.toJSONRPC();
      expect(jsonrpc.data?.toolName).toBe('test-tool');
      expect(jsonrpc.data?.operation).toBe('execute');
    });

    test('NotFoundError should include resource information', () => {
      const error = new NotFoundError('tool', 'non-existent-tool');

      expect(error.code).toBe(-32601);
      expect(error.resourceType).toBe('tool');
      expect(error.resourceId).toBe('non-existent-tool');
      expect(error.message).toBe("tool 'non-existent-tool' not found");

      const jsonrpc = error.toJSONRPC();
      expect(jsonrpc.data?.resourceType).toBe('tool');
      expect(jsonrpc.data?.resourceId).toBe('non-existent-tool');
    });

    test('RateLimitError should include rate limit information', () => {
      const resetTime = new Date(Date.now() + 60000);
      const error = new RateLimitError(100, 60000, resetTime);

      expect(error.code).toBe(-32000);
      expect(error.limit).toBe(100);
      expect(error.windowMs).toBe(60000);
      expect(error.resetTime).toBe(resetTime);
      expect(error.recoverable).toBe(true);

      const jsonrpc = error.toJSONRPC();
      expect(jsonrpc.data?.limit).toBe(100);
      expect(jsonrpc.data?.windowMs).toBe(60000);
      expect(jsonrpc.data?.retryAfter).toBeGreaterThan(0);
    });

    test('TimeoutError should include timeout information', () => {
      const error = new TimeoutError('database-query', 5000);

      expect(error.code).toBe(-32002);
      expect(error.operation).toBe('database-query');
      expect(error.timeoutMs).toBe(5000);
      expect(error.recoverable).toBe(true);
      expect(error.message).toBe("Operation 'database-query' timed out after 5000ms");

      const jsonrpc = error.toJSONRPC();
      expect(jsonrpc.data?.operation).toBe('database-query');
      expect(jsonrpc.data?.timeoutMs).toBe(5000);
    });
  });

  describe('MCPErrorFactory', () => {
    test('should create error from generic Error', () => {
      const originalError = new Error('Generic error');
      originalError.name = 'TypeError';
      
      const mcpError = MCPErrorFactory.fromError(originalError, 'corr-123');

      expect(isMCPError(mcpError)).toBe(true);
      expect(mcpError.message).toBe('Generic error');
      expect(mcpError.correlationId).toBe('corr-123');
      expect(mcpError.context?.originalError).toBe('TypeError');
    });

    test('should return existing MCPError unchanged', () => {
      const originalError = new ToolError('Tool failed', 'test-tool');
      const result = MCPErrorFactory.fromError(originalError);

      expect(result).toBe(originalError);
    });

    test('should create validation error', () => {
      const error = MCPErrorFactory.validation('age', 'not-a-number', 'number');

      expect(error.field).toBe('age');
      expect(error.value).toBe('not-a-number');
      expect(error.message).toContain('age');
      expect(error.message).toContain('number');
    });

    test('should create tool error', () => {
      const error = MCPErrorFactory.toolError(
        'search-tool',
        'execute',
        'Search failed',
        false,
        'corr-123'
      );

      expect(error.toolName).toBe('search-tool');
      expect(error.operation).toBe('execute');
      expect(error.message).toBe('Search failed');
      expect(error.recoverable).toBe(false);
    });

    test('should create not found error', () => {
      const error = MCPErrorFactory.notFound('document', 'doc-123');

      expect(error.resourceType).toBe('document');
      expect(error.resourceId).toBe('doc-123');
    });

    test('should create rate limit error', () => {
      const resetTime = new Date();
      const error = MCPErrorFactory.rateLimit(50, 30000, resetTime);

      expect(error.limit).toBe(50);
      expect(error.windowMs).toBe(30000);
      expect(error.resetTime).toBe(resetTime);
    });

    test('should create timeout error', () => {
      const error = MCPErrorFactory.timeout('api-call', 10000);

      expect(error.operation).toBe('api-call');
      expect(error.timeoutMs).toBe(10000);
    });
  });

  describe('Type Guards', () => {
    test('isMCPError should identify MCP errors correctly', () => {
      const mcpError = new ProtocolError('Test error');
      const regularError = new Error('Regular error');

      expect(isMCPError(mcpError)).toBe(true);
      expect(isMCPError(regularError)).toBe(false);
      expect(isMCPError(null)).toBe(false);
      expect(isMCPError(undefined)).toBe(false);
      expect(isMCPError('string')).toBe(false);
    });

    test('isRecoverableError should identify recoverable errors', () => {
      const recoverableError = new ToolError('Recoverable', 'test-tool', 'execute', true);
      const nonRecoverableError = new ValidationError('Non-recoverable', 'field');
      const regularError = new Error('Regular error');

      expect(isRecoverableError(recoverableError)).toBe(true);
      expect(isRecoverableError(nonRecoverableError)).toBe(false);
      expect(isRecoverableError(regularError)).toBe(false);
    });
  });

  describe('Error Codes', () => {
    test('should have all required error codes', () => {
      expect(ErrorCodes.PARSE_ERROR).toBe(-32700);
      expect(ErrorCodes.INVALID_REQUEST).toBe(-32600);
      expect(ErrorCodes.METHOD_NOT_FOUND).toBe(-32601);
      expect(ErrorCodes.INVALID_PARAMS).toBe(-32602);
      expect(ErrorCodes.INTERNAL_ERROR).toBe(-32603);
      expect(ErrorCodes.RATE_LIMIT_EXCEEDED).toBe(-32000);
      expect(ErrorCodes.TOOL_ERROR).toBe(-32001);
      expect(ErrorCodes.TIMEOUT_ERROR).toBe(-32002);
    });
  });

  describe('Error Inheritance', () => {
    test('should maintain proper inheritance chain', () => {
      const error = new ToolError('Test', 'tool-name');

      expect(error instanceof Error).toBe(true);
      expect(error instanceof MCPError).toBe(true);
      expect(error instanceof ToolError).toBe(true);
      expect(error.name).toBe('ToolError');
    });

    test('should preserve stack trace', () => {
      const error = new ProtocolError('Stack test');

      expect(error.stack).toBeDefined();
      expect(error.stack).toContain('ProtocolError');
    });
  });

  describe('Context and Correlation', () => {
    test('should handle missing correlation ID', () => {
      const error = new ToolError('Test', 'tool-name');

      expect(error.correlationId).toBeUndefined();
    });

    test('should handle missing context', () => {
      const error = new ToolError('Test', 'tool-name', 'execute', true, 'corr-123');

      expect(error.context).toBeUndefined();
    });

    test('should preserve complex context objects', () => {
      const context = {
        user: { id: 123, name: 'Test User' },
        request: { method: 'POST', url: '/api/test' },
        nested: { deep: { value: 'test' } },
      };

      const error = new ProtocolError('Test', -32000, 'corr-123', context);

      expect(error.context).toEqual(context);
    });
  });
});