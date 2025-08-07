/**
 * Base MCP Error Class
 * Provides structured error handling for all MCP operations
 */
export abstract class MCPError extends Error {
  public readonly code: number;
  public readonly timestamp: Date;
  public readonly correlationId: string | undefined;
  public readonly context: Record<string, unknown> | undefined;
  public readonly recoverable: boolean;

  constructor(
    message: string,
    code: number,
    recoverable: boolean = false,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.timestamp = new Date();
    this.correlationId = correlationId;
    this.context = context;
    this.recoverable = recoverable;

    // Maintain proper stack trace for debugging
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }

  /**
   * Convert error to JSON-RPC error format
   */
  toJSONRPC(): {
    code: number;
    message: string;
    data?: Record<string, unknown>;
  } {
    return {
      code: this.code,
      message: this.message,
      data: {
        timestamp: this.timestamp.toISOString(),
        correlationId: this.correlationId,
        context: this.context,
        recoverable: this.recoverable,
        stack: this.stack,
      },
    };
  }

  /**
   * Convert error to structured log format
   */
  toLogFormat(): {
    name: string;
    message: string;
    code: number;
    timestamp: string;
    correlationId: string | undefined;
    context: Record<string, unknown> | undefined;
    recoverable: boolean;
    stack: string | undefined;
  } {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      timestamp: this.timestamp.toISOString(),
      correlationId: this.correlationId,
      context: this.context,
      recoverable: this.recoverable,
      stack: this.stack,
    };
  }
}

/**
 * Protocol-level errors (JSON-RPC related)
 */
export class ProtocolError extends MCPError {
  constructor(
    message: string,
    code: number = -32603,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message, code, false, correlationId, context);
  }
}

/**
 * Invalid request format or parameters
 */
export class ValidationError extends MCPError {
  public readonly field: string | undefined;
  public readonly value: unknown | undefined;

  constructor(
    message: string,
    field?: string,
    value?: unknown,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message, -32602, false, correlationId, context);
    this.field = field;
    this.value = value;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        field: this.field,
        value: this.value,
      },
    };
  }
}

/**
 * Tool-related errors
 */
export class ToolError extends MCPError {
  public readonly toolName: string;
  public readonly operation: string;

  constructor(
    message: string,
    toolName: string,
    operation: string = 'execute',
    recoverable: boolean = true,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message, -32001, recoverable, correlationId, context);
    this.toolName = toolName;
    this.operation = operation;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        toolName: this.toolName,
        operation: this.operation,
      },
    };
  }
}

/**
 * Resource not found errors
 */
export class NotFoundError extends MCPError {
  public readonly resourceType: string;
  public readonly resourceId: string;

  constructor(
    resourceType: string,
    resourceId: string,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    const message = `${resourceType} '${resourceId}' not found`;
    super(message, -32601, false, correlationId, context);
    this.resourceType = resourceType;
    this.resourceId = resourceId;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        resourceType: this.resourceType,
        resourceId: this.resourceId,
      },
    };
  }
}

/**
 * Rate limiting errors
 */
export class RateLimitError extends MCPError {
  public readonly limit: number;
  public readonly windowMs: number;
  public readonly resetTime: Date;

  constructor(
    limit: number,
    windowMs: number,
    resetTime: Date,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    const message = `Rate limit exceeded: ${limit} requests per ${windowMs}ms window`;
    super(message, -32000, true, correlationId, context);
    this.limit = limit;
    this.windowMs = windowMs;
    this.resetTime = resetTime;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        limit: this.limit,
        windowMs: this.windowMs,
        resetTime: this.resetTime.toISOString(),
        retryAfter: Math.ceil((this.resetTime.getTime() - Date.now()) / 1000),
      },
    };
  }
}

/**
 * Authentication/Authorization errors
 */
export class AuthenticationError extends MCPError {
  public readonly authType: string;

  constructor(
    message: string,
    authType: string = 'unknown',
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message, -32005, false, correlationId, context);
    this.authType = authType;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        authType: this.authType,
      },
    };
  }
}

/**
 * Timeout errors
 */
export class TimeoutError extends MCPError {
  public readonly operation: string;
  public readonly timeoutMs: number;

  constructor(
    operation: string,
    timeoutMs: number,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    const message = `Operation '${operation}' timed out after ${timeoutMs}ms`;
    super(message, -32002, true, correlationId, context);
    this.operation = operation;
    this.timeoutMs = timeoutMs;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        operation: this.operation,
        timeoutMs: this.timeoutMs,
      },
    };
  }
}

/**
 * Configuration errors
 */
export class ConfigurationError extends MCPError {
  public readonly configKey: string;
  public readonly expectedType: string | undefined;

  constructor(
    message: string,
    configKey: string,
    expectedType?: string,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message, -32003, false, correlationId, context);
    this.configKey = configKey;
    this.expectedType = expectedType;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        configKey: this.configKey,
        expectedType: this.expectedType,
      },
    };
  }
}

/**
 * Resource limit errors (memory, connections, etc.)
 */
export class ResourceLimitError extends MCPError {
  public readonly resource: string;
  public readonly limit: number;
  public readonly current: number;

  constructor(
    resource: string,
    limit: number,
    current: number,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    const message = `${resource} limit exceeded: ${current}/${limit}`;
    super(message, -32004, true, correlationId, context);
    this.resource = resource;
    this.limit = limit;
    this.current = current;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        resource: this.resource,
        limit: this.limit,
        current: this.current,
      },
    };
  }
}

/**
 * Internal server errors
 */
export class InternalServerError extends MCPError {
  constructor(
    message: string,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    super(message, -32603, false, correlationId, context);
  }
}

/**
 * Dependency injection for error handling
 */
export class DependencyError extends MCPError {
  public readonly dependency: string;

  constructor(
    dependency: string,
    message?: string,
    correlationId?: string,
    context?: Record<string, unknown>
  ) {
    const errorMessage = message || `Required dependency '${dependency}' is not available`;
    super(errorMessage, -32006, false, correlationId, context);
    this.dependency = dependency;
  }

  toJSONRPC() {
    const base = super.toJSONRPC();
    return {
      ...base,
      data: {
        ...base.data,
        dependency: this.dependency,
      },
    };
  }
}

/**
 * Error factory for creating specific error types
 */
export class MCPErrorFactory {
  /**
   * Create error from generic Error with context
   */
  static fromError(
    error: Error,
    correlationId?: string,
    context?: Record<string, unknown>
  ): MCPError {
    if (error instanceof MCPError) {
      return error;
    }

    return new InternalServerError(
      error.message || 'Unknown error occurred',
      correlationId,
      {
        ...context,
        originalError: error.name,
        originalStack: error.stack,
      }
    );
  }

  /**
   * Create validation error for specific field
   */
  static validation(
    field: string,
    value: unknown,
    expectedType?: string,
    correlationId?: string
  ): ValidationError {
    const message = expectedType
      ? `Invalid '${field}': expected ${expectedType}, got ${typeof value}`
      : `Invalid '${field}': ${value}`;

    return new ValidationError(message, field, value, correlationId, {
      expectedType,
    });
  }

  /**
   * Create tool error
   */
  static toolError(
    toolName: string,
    operation: string,
    message: string,
    recoverable: boolean = true,
    correlationId?: string
  ): ToolError {
    return new ToolError(
      message,
      toolName,
      operation,
      recoverable,
      correlationId,
      { toolName, operation }
    );
  }

  /**
   * Create not found error
   */
  static notFound(
    resourceType: string,
    resourceId: string,
    correlationId?: string
  ): NotFoundError {
    return new NotFoundError(resourceType, resourceId, correlationId);
  }

  /**
   * Create rate limit error
   */
  static rateLimit(
    limit: number,
    windowMs: number,
    resetTime: Date,
    correlationId?: string
  ): RateLimitError {
    return new RateLimitError(limit, windowMs, resetTime, correlationId);
  }

  /**
   * Create timeout error
   */
  static timeout(
    operation: string,
    timeoutMs: number,
    correlationId?: string
  ): TimeoutError {
    return new TimeoutError(operation, timeoutMs, correlationId);
  }

  /**
   * Create configuration error
   */
  static config(
    configKey: string,
    message: string,
    expectedType?: string,
    correlationId?: string
  ): ConfigurationError {
    return new ConfigurationError(message, configKey, expectedType, correlationId);
  }

  /**
   * Create resource limit error
   */
  static resourceLimit(
    resource: string,
    limit: number,
    current: number,
    correlationId?: string
  ): ResourceLimitError {
    return new ResourceLimitError(resource, limit, current, correlationId);
  }

  /**
   * Create dependency error
   */
  static dependency(
    dependency: string,
    message?: string,
    correlationId?: string
  ): DependencyError {
    return new DependencyError(dependency, message, correlationId);
  }
}

/**
 * Error code constants for consistency
 */
export const ErrorCodes = {
  // JSON-RPC 2.0 Standard Errors
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,

  // MCP-Specific Errors (32000 to -32099 reserved for implementation-defined server-errors)
  SERVER_ERROR_BASE: -32000,
  RATE_LIMIT_EXCEEDED: -32000,
  TOOL_ERROR: -32001,
  TIMEOUT_ERROR: -32002,
  CONFIGURATION_ERROR: -32003,
  RESOURCE_LIMIT_ERROR: -32004,
  AUTH_ERROR: -32005,
  DEPENDENCY_ERROR: -32006,
} as const;

/**
 * Type guard for MCPError
 */
export function isMCPError(error: unknown): error is MCPError {
  return error instanceof MCPError;
}

/**
 * Type guard for recoverable errors
 */
export function isRecoverableError(error: unknown): boolean {
  return isMCPError(error) && error.recoverable;
}