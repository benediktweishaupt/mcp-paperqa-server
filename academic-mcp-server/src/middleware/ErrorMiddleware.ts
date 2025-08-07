import { EventEmitter } from 'events';
import { MCPError, MCPErrorFactory, isMCPError, isRecoverableError } from '../errors/MCPErrors';
import { MCPLogger } from '../logging/Logger';

/**
 * Error handler function type
 */
export type ErrorHandler = (
  error: MCPError,
  context: ErrorContext,
  recovery?: ErrorRecoveryStrategy
) => Promise<ErrorHandlingResult>;

/**
 * Error context information
 */
export interface ErrorContext {
  correlationId: string;
  requestId?: string;
  method?: string;
  operation?: string;
  timestamp: Date;
  retryCount: number;
  metadata?: Record<string, unknown>;
}

/**
 * Error handling result
 */
export interface ErrorHandlingResult {
  shouldRetry: boolean;
  retryAfterMs?: number;
  transformedError?: MCPError;
  recoveryAction?: string;
  additionalContext?: Record<string, unknown>;
}

/**
 * Error recovery strategy
 */
export interface ErrorRecoveryStrategy {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
  jitterFactor: number;
  recoverableErrorTypes: string[];
}

/**
 * Circuit breaker configuration
 */
export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeoutMs: number;
  monitoringWindowMs: number;
  minimumRequestThreshold: number;
}

/**
 * Circuit breaker state
 */
enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

/**
 * Circuit breaker for preventing cascading failures
 */
class CircuitBreaker {
  private state = CircuitBreakerState.CLOSED;
  private failureCount = 0;
  private requestCount = 0;
  private _lastFailureTime = 0;
  private nextAttemptTime = 0;

  constructor(
    private config: CircuitBreakerConfig,
    private logger: MCPLogger
  ) {}

  /**
   * Check if operation should be allowed
   */
  canExecute(): boolean {
    const now = Date.now();

    switch (this.state) {
      case CircuitBreakerState.CLOSED:
        return true;

      case CircuitBreakerState.OPEN:
        if (now >= this.nextAttemptTime) {
          this.state = CircuitBreakerState.HALF_OPEN;
          this.logger.info('Circuit breaker transitioning to HALF_OPEN', {
            operation: 'circuit_breaker_state_change',
            metadata: { newState: this.state },
          });
          return true;
        }
        return false;

      case CircuitBreakerState.HALF_OPEN:
        return true;

      default:
        return true;
    }
  }

  /**
   * Record operation result
   */
  recordResult(success: boolean): void {
    const now = Date.now();
    this.requestCount++;

    if (success) {
      this.onSuccess();
    } else {
      this.onFailure(now);
    }
  }

  /**
   * Handle successful operation
   */
  private onSuccess(): void {
    this.failureCount = 0;
    
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.CLOSED;
      this.logger.info('Circuit breaker transitioned to CLOSED after successful recovery', {
        operation: 'circuit_breaker_recovery',
        metadata: { newState: this.state },
      });
    }
  }

  /**
   * Handle failed operation
   */
  private onFailure(timestamp: number): void {
    this.failureCount++;
    this._lastFailureTime = timestamp;

    const failureRate = this.requestCount > 0 ? this.failureCount / this.requestCount : 0;
    const hasMinimumRequests = this.requestCount >= this.config.minimumRequestThreshold;

    if (
      hasMinimumRequests &&
      failureRate >= this.config.failureThreshold &&
      this.state !== CircuitBreakerState.OPEN
    ) {
      this.state = CircuitBreakerState.OPEN;
      this.nextAttemptTime = timestamp + this.config.resetTimeoutMs;
      
      this.logger.warn('Circuit breaker opened due to high failure rate', {
        operation: 'circuit_breaker_opened',
        metadata: {
          failureRate,
          failureCount: this.failureCount,
          requestCount: this.requestCount,
          nextAttemptTime: new Date(this.nextAttemptTime).toISOString(),
        },
      });
    }
  }

  /**
   * Get circuit breaker status
   */
  getStatus(): {
    state: CircuitBreakerState;
    failureCount: number;
    requestCount: number;
    failureRate: number;
    nextAttemptTime?: Date | undefined;
  } {
    return {
      state: this.state,
      failureCount: this.failureCount,
      requestCount: this.requestCount,
      failureRate: this.requestCount > 0 ? this.failureCount / this.requestCount : 0,
      nextAttemptTime: this.nextAttemptTime > 0 ? new Date(this.nextAttemptTime) : undefined,
    };
  }

  /**
   * Reset circuit breaker
   */
  reset(): void {
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.requestCount = 0;
    this._lastFailureTime = 0;
    this.nextAttemptTime = 0;
    
    this.logger.info('Circuit breaker manually reset', {
      operation: 'circuit_breaker_reset',
    });
  }
}

/**
 * Error middleware events
 */
export interface ErrorMiddlewareEvents {
  'error-handled': (error: MCPError, context: ErrorContext, result: ErrorHandlingResult) => void;
  'retry-attempted': (error: MCPError, context: ErrorContext, attempt: number) => void;
  'circuit-breaker-opened': (operation: string) => void;
  'circuit-breaker-closed': (operation: string) => void;
  'error-recovery-failed': (error: MCPError, context: ErrorContext) => void;
}

/**
 * Error Middleware Configuration
 */
export interface ErrorMiddlewareConfig {
  enableRetries: boolean;
  enableCircuitBreaker: boolean;
  defaultRecoveryStrategy: ErrorRecoveryStrategy;
  circuitBreakerConfig: CircuitBreakerConfig;
  errorHandlers: Map<string, ErrorHandler>;
}

/**
 * Error Middleware for MCP operations
 * Provides comprehensive error handling with retries, circuit breakers, and recovery strategies
 */
export class ErrorMiddleware extends EventEmitter {
  private config: ErrorMiddlewareConfig;
  private logger: MCPLogger;
  private circuitBreakers = new Map<string, CircuitBreaker>();
  private retryAttempts = new Map<string, number>();

  constructor(logger: MCPLogger, config: Partial<ErrorMiddlewareConfig> = {}) {
    super();
    
    this.logger = logger;
    this.config = {
      enableRetries: true,
      enableCircuitBreaker: true,
      defaultRecoveryStrategy: {
        maxRetries: 3,
        baseDelayMs: 1000,
        maxDelayMs: 30000,
        backoffMultiplier: 2,
        jitterFactor: 0.1,
        recoverableErrorTypes: ['ToolError', 'TimeoutError', 'RateLimitError'],
      },
      circuitBreakerConfig: {
        failureThreshold: 0.5, // 50% failure rate
        resetTimeoutMs: 30000, // 30 seconds
        monitoringWindowMs: 60000, // 1 minute
        minimumRequestThreshold: 10,
      },
      errorHandlers: new Map(),
      ...config,
    };
  }

  /**
   * Register custom error handler
   */
  registerErrorHandler(errorType: string, handler: ErrorHandler): void {
    this.config.errorHandlers.set(errorType, handler);
    this.logger.debug('Error handler registered', {
      operation: 'error_handler_registration',
      metadata: { errorType },
    });
  }

  /**
   * Unregister error handler
   */
  unregisterErrorHandler(errorType: string): boolean {
    const removed = this.config.errorHandlers.delete(errorType);
    if (removed) {
      this.logger.debug('Error handler unregistered', {
        operation: 'error_handler_unregistration',
        metadata: { errorType },
      });
    }
    return removed;
  }

  /**
   * Handle error with recovery strategies
   */
  async handleError(
    error: Error | MCPError,
    context: Partial<ErrorContext> = {}
  ): Promise<ErrorHandlingResult> {
    const mcpError = isMCPError(error) ? error : MCPErrorFactory.fromError(error);
    
    const fullContext: ErrorContext = {
      correlationId: context.correlationId || this.logger.generateCorrelationId(),
      timestamp: new Date(),
      retryCount: 0,
      ...context,
    };

    // Log the error
    this.logger.error('Error occurred', mcpError, {
      correlationId: fullContext.correlationId,
      ...(fullContext.method && { method: fullContext.method }),
      ...(fullContext.operation && { operation: fullContext.operation }),
      metadata: { retryCount: fullContext.retryCount },
    });

    // Check circuit breaker
    if (this.config.enableCircuitBreaker && fullContext.operation) {
      const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
      if (!circuitBreaker.canExecute()) {
        const result: ErrorHandlingResult = {
          shouldRetry: false,
          transformedError: MCPErrorFactory.resourceLimit(
            'circuit_breaker',
            1,
            0,
            fullContext.correlationId
          ),
          recoveryAction: 'circuit_breaker_open',
        };

        this.emit('error-handled', mcpError, fullContext, result);
        return result;
      }
    }

    // Try custom error handler first
    const customHandler = this.config.errorHandlers.get(mcpError.constructor.name);
    if (customHandler) {
      try {
        const result = await customHandler(
          mcpError,
          fullContext,
          this.config.defaultRecoveryStrategy
        );
        
        this.emit('error-handled', mcpError, fullContext, result);
        return result;
      } catch (handlerError) {
        this.logger.error('Custom error handler failed', handlerError as Error, {
          correlationId: fullContext.correlationId,
        });
      }
    }

    // Use default error handling strategy
    const result = await this.defaultErrorHandling(mcpError, fullContext);
    
    // Record circuit breaker result
    if (this.config.enableCircuitBreaker && fullContext.operation) {
      const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
      circuitBreaker.recordResult(!result.shouldRetry || result.transformedError === undefined);
    }

    this.emit('error-handled', mcpError, fullContext, result);
    return result;
  }

  /**
   * Execute operation with error handling
   */
  async executeWithErrorHandling<T>(
    operation: () => Promise<T>,
    context: Partial<ErrorContext> = {}
  ): Promise<T> {
    const fullContext: ErrorContext = {
      correlationId: context.correlationId || this.logger.generateCorrelationId(),
      timestamp: new Date(),
      retryCount: 0,
      ...context,
    };

    let lastError: MCPError | null = null;
    const maxRetries = this.config.defaultRecoveryStrategy.maxRetries;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        fullContext.retryCount = attempt;
        
        // Check circuit breaker before execution
        if (this.config.enableCircuitBreaker && fullContext.operation) {
          const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
          if (!circuitBreaker.canExecute()) {
            throw MCPErrorFactory.resourceLimit(
              'circuit_breaker',
              1,
              0,
              fullContext.correlationId
            );
          }
        }

        const result = await operation();
        
        // Record success in circuit breaker
        if (this.config.enableCircuitBreaker && fullContext.operation) {
          const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
          circuitBreaker.recordResult(true);
        }

        return result;

      } catch (error) {
        lastError = isMCPError(error) ? error : MCPErrorFactory.fromError(error as Error);
        
        // Record failure in circuit breaker
        if (this.config.enableCircuitBreaker && fullContext.operation) {
          const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
          circuitBreaker.recordResult(false);
        }

        // Handle the error and decide on retry
        const handlingResult = await this.handleError(lastError, fullContext);
        
        if (!handlingResult.shouldRetry || attempt >= maxRetries) {
          throw handlingResult.transformedError || lastError;
        }

        // Calculate retry delay
        if (handlingResult.retryAfterMs) {
          await this.delay(handlingResult.retryAfterMs);
        } else {
          const delay = this.calculateRetryDelay(attempt);
          await this.delay(delay);
        }

        this.emit('retry-attempted', lastError, fullContext, attempt + 1);
        this.logger.info('Retrying operation', {
          correlationId: fullContext.correlationId,
          ...(fullContext.operation && { operation: fullContext.operation }),
          metadata: { attempt: attempt + 1, maxRetries },
        });
      }
    }

    throw lastError || new Error('Operation failed without specific error');
  }

  /**
   * Default error handling strategy
   */
  private async defaultErrorHandling(
    error: MCPError,
    context: ErrorContext
  ): Promise<ErrorHandlingResult> {
    // Check if error is recoverable
    if (!isRecoverableError(error)) {
      return {
        shouldRetry: false,
        transformedError: error,
        recoveryAction: 'no_recovery',
      };
    }

    // Check retry count
    if (context.retryCount >= this.config.defaultRecoveryStrategy.maxRetries) {
      return {
        shouldRetry: false,
        transformedError: error,
        recoveryAction: 'max_retries_exceeded',
      };
    }

    // Check if error type is retryable
    const isRetryable = this.config.defaultRecoveryStrategy.recoverableErrorTypes.includes(
      error.constructor.name
    );

    if (!isRetryable) {
      return {
        shouldRetry: false,
        transformedError: error,
        recoveryAction: 'error_type_not_retryable',
      };
    }

    // Calculate retry delay
    const retryDelay = this.calculateRetryDelay(context.retryCount);

    return {
      shouldRetry: true,
      retryAfterMs: retryDelay,
      recoveryAction: 'retry_with_backoff',
      additionalContext: {
        retryDelay,
        attempt: context.retryCount + 1,
        maxRetries: this.config.defaultRecoveryStrategy.maxRetries,
      },
    };
  }

  /**
   * Calculate retry delay with exponential backoff and jitter
   */
  private calculateRetryDelay(attempt: number): number {
    const { baseDelayMs, maxDelayMs, backoffMultiplier, jitterFactor } = this.config.defaultRecoveryStrategy;
    
    // Exponential backoff
    const delay = Math.min(baseDelayMs * Math.pow(backoffMultiplier, attempt), maxDelayMs);
    
    // Add jitter to prevent thundering herd
    const jitter = delay * jitterFactor * Math.random();
    
    return Math.floor(delay + jitter);
  }

  /**
   * Get or create circuit breaker for operation
   */
  private getOrCreateCircuitBreaker(operation: string): CircuitBreaker {
    let circuitBreaker = this.circuitBreakers.get(operation);
    
    if (!circuitBreaker) {
      circuitBreaker = new CircuitBreaker(this.config.circuitBreakerConfig, this.logger);
      this.circuitBreakers.set(operation, circuitBreaker);
      
      this.logger.debug('Circuit breaker created', {
        operation: 'circuit_breaker_created',
        metadata: { operation },
      });
    }
    
    return circuitBreaker;
  }

  /**
   * Delay execution
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get circuit breaker status for operation
   */
  getCircuitBreakerStatus(operation: string): ReturnType<CircuitBreaker['getStatus']> | null {
    const circuitBreaker = this.circuitBreakers.get(operation);
    return circuitBreaker ? circuitBreaker.getStatus() : null;
  }

  /**
   * Reset circuit breaker for operation
   */
  resetCircuitBreaker(operation: string): boolean {
    const circuitBreaker = this.circuitBreakers.get(operation);
    if (circuitBreaker) {
      circuitBreaker.reset();
      return true;
    }
    return false;
  }

  /**
   * Get middleware statistics
   */
  getStats(): {
    activeCircuitBreakers: number;
    totalErrorHandlers: number;
    circuitBreakerStatuses: Record<string, ReturnType<CircuitBreaker['getStatus']>>;
  } {
    const circuitBreakerStatuses: Record<string, ReturnType<CircuitBreaker['getStatus']>> = {};
    
    for (const [operation, breaker] of this.circuitBreakers.entries()) {
      circuitBreakerStatuses[operation] = breaker.getStatus();
    }

    return {
      activeCircuitBreakers: this.circuitBreakers.size,
      totalErrorHandlers: this.config.errorHandlers.size,
      circuitBreakerStatuses,
    };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<ErrorMiddlewareConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.logger.info('Error middleware configuration updated', {
      operation: 'config_update',
    });
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.circuitBreakers.clear();
    this.retryAttempts.clear();
    this.removeAllListeners();
  }

  /**
   * Typed event emitter methods
   */
  emit<K extends keyof ErrorMiddlewareEvents>(
    event: K,
    ...args: Parameters<ErrorMiddlewareEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }

  on<K extends keyof ErrorMiddlewareEvents>(
    event: K,
    listener: ErrorMiddlewareEvents[K]
  ): this {
    return super.on(event, listener);
  }

  off<K extends keyof ErrorMiddlewareEvents>(
    event: K,
    listener: ErrorMiddlewareEvents[K]
  ): this {
    return super.off(event, listener);
  }
}