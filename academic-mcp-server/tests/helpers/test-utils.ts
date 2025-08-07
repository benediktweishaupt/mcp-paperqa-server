/**
 * Test utilities and helpers for MCP server testing
 */

import { EventEmitter } from 'events';
import { AcademicMCPServer } from '../../src/server/AcademicMCPServer';
import { ToolMetadata, ToolHandler, ToolRegistration } from '../../src/tools/types';

/**
 * Create a test server instance with common test configuration
 */
export function createTestServer(overrides: Partial<any> = {}): AcademicMCPServer {
  return new AcademicMCPServer({
    name: 'test-server',
    version: '1.0.0-test',
    description: 'Test MCP server instance',
    enableHealthCheck: true,
    maxConnections: 1,
    ...overrides,
  });
}

/**
 * Create a test tool registration
 */
export function createTestTool(
  name: string,
  handler?: ToolHandler,
  metadata?: Partial<ToolMetadata>
): ToolRegistration {
  const defaultHandler: ToolHandler = async () => ({
    result: `Test result from ${name}`,
    timestamp: new Date().toISOString(),
  });

  return {
    name,
    handler: handler || defaultHandler,
    metadata: {
      description: `Test tool: ${name}`,
      category: 'test',
      version: '1.0.0',
      author: 'Test Suite',
      inputSchema: {
        type: 'object',
        properties: {
          input: {
            type: 'string',
            description: 'Test input parameter',
          },
        },
      },
      ...metadata,
    },
    permissions: {
      requiresAuth: false,
      allowedRoles: ['*'],
    },
    rateLimit: {
      requests: 100,
      windowMs: 60000,
    },
  };
}

/**
 * Mock MCP request context
 */
export function createMockContext(overrides: any = {}) {
  return {
    requestId: 'test-req-123',
    timestamp: new Date(),
    metadata: {},
    ...overrides,
  };
}

/**
 * Mock JSON-RPC request
 */
export function createMockRequest(
  method: string,
  params: any = {},
  id: string | number = 1
) {
  return {
    jsonrpc: '2.0' as const,
    id,
    method,
    params,
  };
}

/**
 * Wait for event emitter to emit specific event
 */
export function waitForEvent(
  emitter: EventEmitter,
  eventName: string,
  timeout: number = 5000
): Promise<any> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Timeout waiting for event: ${eventName}`));
    }, timeout);

    emitter.once(eventName, (...args) => {
      clearTimeout(timer);
      resolve(args.length === 1 ? args[0] : args);
    });
  });
}

/**
 * Wait for multiple events in sequence
 */
export async function waitForEvents(
  emitter: EventEmitter,
  events: string[],
  timeout: number = 5000
): Promise<any[]> {
  const results: any[] = [];
  
  for (const eventName of events) {
    const result = await waitForEvent(emitter, eventName, timeout);
    results.push(result);
  }
  
  return results;
}

/**
 * Delay helper for tests
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create mock logger for testing
 */
export function createMockLogger() {
  return {
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn(),
    generateCorrelationId: jest.fn(() => 'test-correlation-123'),
    logRequestStart: jest.fn(),
    logRequestEnd: jest.fn(),
    startPerformanceTracking: jest.fn(() => 'test-tracking-123'),
    endPerformanceTracking: jest.fn(),
    logToolExecution: jest.fn(),
    logServerEvent: jest.fn(),
    logProtocolEvent: jest.fn(),
    child: jest.fn(() => createMockLogger()),
    setLogLevel: jest.fn(),
    getConfig: jest.fn(() => ({ level: 'debug' })),
    getStats: jest.fn(() => ({ activePerformanceTracking: 0 })),
    cleanup: jest.fn(),
  };
}

/**
 * Test fixture data
 */
export const testData = {
  samplePdfContent: 'Sample PDF content for testing',
  sampleCitation: {
    title: 'Test Article',
    authors: ['Test Author'],
    journal: 'Test Journal',
    year: 2024,
    pages: '1-10',
  },
  sampleQuery: 'What is systems theory?',
  sampleResponse: {
    passages: [
      {
        text: 'Systems theory is a conceptual framework...',
        source: 'test-document.pdf',
        page: 1,
        relevance: 0.85,
      },
    ],
    metadata: {
      queryTime: 250,
      totalDocuments: 1,
    },
  },
};

/**
 * Assertion helpers
 */
export const assertions = {
  /**
   * Assert that response has expected MCP format
   */
  isValidMCPResponse(response: any) {
    expect(response).toMatchObject({
      jsonrpc: '2.0',
    });
    expect(response).toHaveProperty('id');
    expect(response).toSatisfy((r: any) => 
      'result' in r || 'error' in r
    );
  },

  /**
   * Assert tool metadata structure
   */
  isValidToolMetadata(metadata: any) {
    expect(metadata).toMatchObject({
      name: expect.any(String),
      description: expect.any(String),
      inputSchema: expect.any(Object),
    });
  },

  /**
   * Assert error response format
   */
  isValidErrorResponse(response: any) {
    expect(response).toMatchObject({
      jsonrpc: '2.0',
      id: expect.anything(),
      error: {
        code: expect.any(Number),
        message: expect.any(String),
      },
    });
  },
};

/**
 * Test environment setup
 */
export function setupTestEnvironment() {
  // Mock console methods to reduce test noise
  const originalConsole = { ...console };
  
  beforeAll(() => {
    console.log = jest.fn();
    console.info = jest.fn();
    console.warn = jest.fn();
    console.error = jest.fn();
  });

  afterAll(() => {
    Object.assign(console, originalConsole);
  });
}

/**
 * Database/persistence test helpers (for future phases)
 */
export const persistenceHelpers = {
  createTempDirectory: () => '/tmp/test-academic-mcp-' + Date.now(),
  cleanupTempFiles: (path: string) => {
    // Implementation for cleanup when file operations are added
  },
  createMockPdfFile: (content: string) => {
    // Implementation for mock PDF creation when PDF processing is added
  },
};