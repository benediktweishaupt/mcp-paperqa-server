import { ToolRegistry } from '../../src/tools/ToolRegistry';
import { ToolRegistration, ToolContext } from '../../src/tools/types';

describe('ToolRegistry', () => {
  let registry: ToolRegistry;

  beforeEach(() => {
    registry = new ToolRegistry({
      enableValidation: true,
      enablePermissions: false,
      enableRateLimit: false,
      maxTools: 10,
    });
  });

  const sampleTool: ToolRegistration = {
    metadata: {
      name: 'test_tool',
      description: 'A test tool for unit tests',
      version: '1.0.0',
      category: 'test',
      inputSchema: {
        type: 'object',
        properties: {
          message: { type: 'string' },
        },
        required: ['message'],
      },
    },
    handler: async (args) => ({
      content: [{ type: 'text', text: `Hello: ${args.message}` }],
    }),
  };

  describe('Tool Registration', () => {
    test('should register a valid tool', async () => {
      await expect(registry.registerTool(sampleTool)).resolves.not.toThrow();
      expect(registry.hasTools('test_tool')).toBe(true);
      expect(registry.getToolCount()).toBe(1);
    });

    test('should emit registration event', async () => {
      const listener = jest.fn();
      registry.on('tool-registered', listener);

      await registry.registerTool(sampleTool);
      
      expect(listener).toHaveBeenCalledWith('test_tool', sampleTool.metadata);
    });

    test('should reject duplicate tool names', async () => {
      await registry.registerTool(sampleTool);
      
      await expect(registry.registerTool(sampleTool))
        .rejects.toThrow("Tool 'test_tool' is already registered");
    });

    test('should reject invalid tools when validation enabled', async () => {
      const invalidTool: ToolRegistration = {
        metadata: {
          name: '', // Invalid name
          description: 'Invalid tool',
          version: '1.0.0',
          inputSchema: { type: 'object' },
        },
        handler: async () => ({ content: [] }),
      };

      await expect(registry.registerTool(invalidTool))
        .rejects.toThrow('Tool validation failed');
    });

    test('should enforce max tools limit', async () => {
      const smallRegistry = new ToolRegistry({ maxTools: 1 });
      
      await smallRegistry.registerTool(sampleTool);
      
      const anotherTool: ToolRegistration = {
        ...sampleTool,
        metadata: { ...sampleTool.metadata, name: 'another_tool' },
      };

      await expect(smallRegistry.registerTool(anotherTool))
        .rejects.toThrow('Tool registry is full (max: 1)');
    });
  });

  describe('Tool Unregistration', () => {
    beforeEach(async () => {
      await registry.registerTool(sampleTool);
    });

    test('should unregister existing tool', async () => {
      const result = await registry.unregisterTool('test_tool');
      expect(result).toBe(true);
      expect(registry.hasTools('test_tool')).toBe(false);
      expect(registry.getToolCount()).toBe(0);
    });

    test('should emit unregistration event', async () => {
      const listener = jest.fn();
      registry.on('tool-unregistered', listener);

      await registry.unregisterTool('test_tool');
      
      expect(listener).toHaveBeenCalledWith('test_tool');
    });

    test('should return false for non-existent tool', async () => {
      const result = await registry.unregisterTool('non_existent');
      expect(result).toBe(false);
    });
  });

  describe('Tool Discovery', () => {
    beforeEach(async () => {
      await registry.registerTool(sampleTool);
      
      const categorizedTool: ToolRegistration = {
        ...sampleTool,
        metadata: {
          ...sampleTool.metadata,
          name: 'categorized_tool',
          category: 'academic',
          tags: ['research', 'analysis'],
        },
      };
      await registry.registerTool(categorizedTool);
    });

    test('should get all tools metadata', () => {
      const allTools = registry.getAllToolsMetadata();
      expect(allTools).toHaveLength(2);
      expect(allTools.map(t => t.name)).toContain('test_tool');
      expect(allTools.map(t => t.name)).toContain('categorized_tool');
    });

    test('should get tools by category', () => {
      const testTools = registry.getToolsByCategory('test');
      expect(testTools).toHaveLength(1);
      expect(testTools[0].name).toBe('test_tool');

      const academicTools = registry.getToolsByCategory('academic');
      expect(academicTools).toHaveLength(1);
      expect(academicTools[0].name).toBe('categorized_tool');
    });

    test('should get tools by tag', () => {
      const researchTools = registry.getToolsByTag('research');
      expect(researchTools).toHaveLength(1);
      expect(researchTools[0].name).toBe('categorized_tool');
    });

    test('should search tools by name and description', () => {
      const searchResults = registry.searchTools('test');
      expect(searchResults).toHaveLength(2); // Both contain 'test'

      const specificResults = registry.searchTools('categorized');
      expect(specificResults).toHaveLength(1);
      expect(specificResults[0].name).toBe('categorized_tool');
    });

    test('should get registry statistics', () => {
      const stats = registry.getStats();
      expect(stats.totalTools).toBe(2);
      expect(stats.categoryCounts.test).toBe(1);
      expect(stats.categoryCounts.academic).toBe(1);
      expect(stats.deprecatedTools).toHaveLength(0);
      expect(stats.experimentalTools).toHaveLength(0);
    });
  });

  describe('Tool Execution', () => {
    const mockContext: ToolContext = {
      requestId: 'test-request-123',
      timestamp: new Date(),
      metadata: { test: true },
    };

    beforeEach(async () => {
      await registry.registerTool(sampleTool);
    });

    test('should execute tool successfully', async () => {
      const result = await registry.executeTool('test_tool', { message: 'world' }, mockContext);
      
      expect(result.content).toHaveLength(1);
      expect(result.content[0]).toEqual({
        type: 'text',
        text: 'Hello: world',
      });
    });

    test('should emit tool execution events', async () => {
      const calledListener = jest.fn();
      registry.on('tool-called', calledListener);

      await registry.executeTool('test_tool', { message: 'test' }, mockContext);
      
      expect(calledListener).toHaveBeenCalledWith('test_tool', mockContext);
    });

    test('should throw for non-existent tool', async () => {
      await expect(registry.executeTool('non_existent', {}, mockContext))
        .rejects.toThrow("Tool 'non_existent' not found");
    });

    test('should validate arguments when validation enabled', async () => {
      await expect(registry.executeTool('test_tool', {}, mockContext))
        .rejects.toThrow("Argument validation failed");
    });

    test('should handle tool execution errors', async () => {
      const errorTool: ToolRegistration = {
        metadata: {
          name: 'error_tool',
          description: 'Tool that throws errors',
          version: '1.0.0',
          inputSchema: { type: 'object' },
        },
        handler: async () => {
          throw new Error('Tool execution failed');
        },
      };

      await registry.registerTool(errorTool);

      const errorListener = jest.fn();
      registry.on('tool-error', errorListener);

      await expect(registry.executeTool('error_tool', {}, mockContext))
        .rejects.toThrow('Tool execution failed');
      
      expect(errorListener).toHaveBeenCalled();
    });
  });

  describe('Rate Limiting', () => {
    const rateLimitedTool: ToolRegistration = {
      ...sampleTool,
      metadata: { ...sampleTool.metadata, name: 'rate_limited_tool' },
      rateLimit: { requests: 2, windowMs: 1000 },
    };

    beforeEach(async () => {
      // Create registry with rate limiting enabled
      registry = new ToolRegistry({
        enableRateLimit: true,
        enableValidation: false,
      });
      await registry.registerTool(rateLimitedTool);
    });

    test('should allow requests within rate limit', async () => {
      const context: ToolContext = {
        requestId: 'test-1',
        timestamp: new Date(),
        metadata: {},
      };

      // First two requests should succeed
      await expect(registry.executeTool('rate_limited_tool', { message: 'test1' }, context))
        .resolves.toBeDefined();
      await expect(registry.executeTool('rate_limited_tool', { message: 'test2' }, context))
        .resolves.toBeDefined();
    });

    test('should reject requests exceeding rate limit', async () => {
      const context: ToolContext = {
        requestId: 'test-1',
        timestamp: new Date(),
        metadata: {},
      };

      // Use up the rate limit
      await registry.executeTool('rate_limited_tool', { message: 'test1' }, context);
      await registry.executeTool('rate_limited_tool', { message: 'test2' }, context);

      // Third request should be rate limited
      await expect(registry.executeTool('rate_limited_tool', { message: 'test3' }, context))
        .rejects.toThrow("Rate limit exceeded for tool 'rate_limited_tool'");
    });
  });

  describe('Configuration Management', () => {
    test('should get current configuration', () => {
      const config = registry.getConfig();
      expect(config.enableValidation).toBe(true);
      expect(config.maxTools).toBe(10);
    });

    test('should update configuration', () => {
      registry.updateConfig({ maxTools: 20, enableRateLimit: true });
      
      const config = registry.getConfig();
      expect(config.maxTools).toBe(20);
      expect(config.enableRateLimit).toBe(true);
      expect(config.enableValidation).toBe(true); // Should retain existing values
    });
  });

  describe('Registry Management', () => {
    beforeEach(async () => {
      await registry.registerTool(sampleTool);
    });

    test('should clear all tools', () => {
      const unregisterListener = jest.fn();
      registry.on('tool-unregistered', unregisterListener);

      registry.clear();
      
      expect(registry.getToolCount()).toBe(0);
      expect(registry.hasTools('test_tool')).toBe(false);
      expect(unregisterListener).toHaveBeenCalledWith('test_tool');
    });

    test('should validate all registered tools', () => {
      const results = registry.validateAllTools();
      
      expect(results).toHaveProperty('test_tool');
      expect(results.test_tool.valid).toBe(true);
    });
  });
});