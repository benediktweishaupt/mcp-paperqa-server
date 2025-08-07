import { ToolValidator } from '../../src/tools/ToolValidator';
import { ToolRegistration, ToolMetadata, ToolParameterSchema } from '../../src/tools/types';

describe('ToolValidator', () => {
  describe('validateMetadata', () => {
    test('should validate valid metadata', () => {
      const metadata: ToolMetadata = {
        name: 'test_tool',
        description: 'A test tool',
        version: '1.0.0',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      };

      const result = ToolValidator.validateMetadata(metadata);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should reject invalid tool name', () => {
      const metadata: ToolMetadata = {
        name: '123invalid',
        description: 'A test tool',
        version: '1.0.0',
        inputSchema: { type: 'object' },
      };

      const result = ToolValidator.validateMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain(
        'Tool name must start with a letter and contain only letters, numbers, underscores, and hyphens'
      );
    });

    test('should reject missing required fields', () => {
      const metadata = {
        name: 'test_tool',
      } as ToolMetadata;

      const result = ToolValidator.validateMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Tool description is required and must be a string');
      expect(result.errors).toContain('Tool version is required and must be a string');
    });

    test('should warn about non-semantic version', () => {
      const metadata: ToolMetadata = {
        name: 'test_tool',
        description: 'A test tool',
        version: 'v1',
        inputSchema: { type: 'object' },
      };

      const result = ToolValidator.validateMetadata(metadata);
      expect(result.valid).toBe(true);
      expect(result.warnings).toContain('Tool version should follow semantic versioning (e.g., 1.0.0)');
    });
  });

  describe('validateParameterSchema', () => {
    test('should validate object schema', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          name: { type: 'string', minLength: 1 },
          age: { type: 'number', minimum: 0 },
        },
        required: ['name'],
      };

      const result = ToolValidator.validateParameterSchema(schema);
      expect(result.valid).toBe(true);
    });

    test('should validate array schema', () => {
      const schema: ToolParameterSchema = {
        type: 'array',
        items: { type: 'string' },
      };

      const result = ToolValidator.validateParameterSchema(schema);
      expect(result.valid).toBe(true);
    });

    test('should reject invalid type', () => {
      const schema = {
        type: 'invalid',
      } as unknown as ToolParameterSchema;

      const result = ToolValidator.validateParameterSchema(schema);
      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain('Invalid schema type: invalid');
    });

    test('should validate string constraints', () => {
      const schema: ToolParameterSchema = {
        type: 'string',
        minLength: 5,
        maxLength: 3, // Invalid: min > max
      };

      const result = ToolValidator.validateParameterSchema(schema);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('String minLength cannot be greater than maxLength');
    });

    test('should validate nested object properties', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          nested: {
            type: 'object',
            properties: {
              invalid: { type: 'invalid' } as unknown as ToolParameterSchema,
            },
          },
        },
      };

      const result = ToolValidator.validateParameterSchema(schema);
      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain("Property 'nested': Property 'invalid': Invalid schema type");
    });
  });

  describe('validateRegistration', () => {
    const validRegistration: ToolRegistration = {
      metadata: {
        name: 'test_tool',
        description: 'A test tool',
        version: '1.0.0',
        inputSchema: { type: 'object' },
      },
      handler: async () => ({ content: [{ type: 'text', text: 'test' }] }),
    };

    test('should validate complete registration', () => {
      const result = ToolValidator.validateRegistration(validRegistration);
      expect(result.valid).toBe(true);
    });

    test('should reject non-function handler', () => {
      const registration = {
        ...validRegistration,
        handler: 'not a function',
      } as unknown as ToolRegistration;

      const result = ToolValidator.validateRegistration(registration);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Tool handler must be a function');
    });

    test('should validate permissions array', () => {
      const registration: ToolRegistration = {
        ...validRegistration,
        permissions: ['read', 'write'],
      };

      const result = ToolValidator.validateRegistration(registration);
      expect(result.valid).toBe(true);
    });

    test('should reject invalid permissions', () => {
      const registration: ToolRegistration = {
        ...validRegistration,
        permissions: ['read', ''] as string[],
      };

      const result = ToolValidator.validateRegistration(registration);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Permission at index 1 must be a non-empty string');
    });

    test('should validate rate limit', () => {
      const registration: ToolRegistration = {
        ...validRegistration,
        rateLimit: { requests: 10, windowMs: 60000 },
      };

      const result = ToolValidator.validateRegistration(registration);
      expect(result.valid).toBe(true);
    });

    test('should reject invalid rate limit', () => {
      const registration: ToolRegistration = {
        ...validRegistration,
        rateLimit: { requests: -1, windowMs: 60000 },
      };

      const result = ToolValidator.validateRegistration(registration);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Rate limit requests must be a positive number');
    });
  });

  describe('validateArguments', () => {
    test('should validate arguments against schema', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          name: { type: 'string' },
          count: { type: 'number', minimum: 0 },
        },
        required: ['name'],
      };

      const args = { name: 'test', count: 5 };
      const result = ToolValidator.validateArguments(args, schema);
      expect(result.valid).toBe(true);
    });

    test('should reject missing required properties', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          name: { type: 'string' },
        },
        required: ['name'],
      };

      const args = {};
      const result = ToolValidator.validateArguments(args, schema);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain("Required property 'name' is missing");
    });

    test('should reject unknown properties', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          name: { type: 'string' },
        },
      };

      const args = { name: 'test', unknown: 'value' };
      const result = ToolValidator.validateArguments(args, schema);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain("Unknown property 'unknown'");
    });

    test('should validate property types', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          count: { type: 'number' },
        },
      };

      const args = { count: 'not a number' };
      const result = ToolValidator.validateArguments(args, schema);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('count: Expected number, got string');
    });

    test('should validate enum values', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          status: { type: 'string', enum: ['active', 'inactive'] },
        },
      };

      const args = { status: 'invalid' };
      const result = ToolValidator.validateArguments(args, schema);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('status: Value must be one of: active, inactive');
    });

    test('should validate string constraints', () => {
      const schema: ToolParameterSchema = {
        type: 'object',
        properties: {
          name: { type: 'string', minLength: 3, maxLength: 10 },
        },
      };

      const shortArgs = { name: 'ab' };
      const shortResult = ToolValidator.validateArguments(shortArgs, schema);
      expect(shortResult.valid).toBe(false);
      expect(shortResult.errors).toContain('name: String must be at least 3 characters');

      const longArgs = { name: 'this is too long' };
      const longResult = ToolValidator.validateArguments(longArgs, schema);
      expect(longResult.valid).toBe(false);
      expect(longResult.errors).toContain('name: String must not exceed 10 characters');
    });
  });
});