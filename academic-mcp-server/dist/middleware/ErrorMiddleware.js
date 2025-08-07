"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ErrorMiddleware = void 0;
const events_1 = require("events");
const MCPErrors_1 = require("../errors/MCPErrors");
var CircuitBreakerState;
(function (CircuitBreakerState) {
    CircuitBreakerState["CLOSED"] = "closed";
    CircuitBreakerState["OPEN"] = "open";
    CircuitBreakerState["HALF_OPEN"] = "half_open";
})(CircuitBreakerState || (CircuitBreakerState = {}));
class CircuitBreaker {
    constructor(config, logger) {
        this.config = config;
        this.logger = logger;
        this.state = CircuitBreakerState.CLOSED;
        this.failureCount = 0;
        this.requestCount = 0;
        this._lastFailureTime = 0;
        this.nextAttemptTime = 0;
    }
    canExecute() {
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
    recordResult(success) {
        const now = Date.now();
        this.requestCount++;
        if (success) {
            this.onSuccess();
        }
        else {
            this.onFailure(now);
        }
    }
    onSuccess() {
        this.failureCount = 0;
        if (this.state === CircuitBreakerState.HALF_OPEN) {
            this.state = CircuitBreakerState.CLOSED;
            this.logger.info('Circuit breaker transitioned to CLOSED after successful recovery', {
                operation: 'circuit_breaker_recovery',
                metadata: { newState: this.state },
            });
        }
    }
    onFailure(timestamp) {
        this.failureCount++;
        this._lastFailureTime = timestamp;
        const failureRate = this.requestCount > 0 ? this.failureCount / this.requestCount : 0;
        const hasMinimumRequests = this.requestCount >= this.config.minimumRequestThreshold;
        if (hasMinimumRequests &&
            failureRate >= this.config.failureThreshold &&
            this.state !== CircuitBreakerState.OPEN) {
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
    getStatus() {
        return {
            state: this.state,
            failureCount: this.failureCount,
            requestCount: this.requestCount,
            failureRate: this.requestCount > 0 ? this.failureCount / this.requestCount : 0,
            nextAttemptTime: this.nextAttemptTime > 0 ? new Date(this.nextAttemptTime) : undefined,
        };
    }
    reset() {
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
class ErrorMiddleware extends events_1.EventEmitter {
    constructor(logger, config = {}) {
        super();
        this.circuitBreakers = new Map();
        this.retryAttempts = new Map();
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
                failureThreshold: 0.5,
                resetTimeoutMs: 30000,
                monitoringWindowMs: 60000,
                minimumRequestThreshold: 10,
            },
            errorHandlers: new Map(),
            ...config,
        };
    }
    registerErrorHandler(errorType, handler) {
        this.config.errorHandlers.set(errorType, handler);
        this.logger.debug('Error handler registered', {
            operation: 'error_handler_registration',
            metadata: { errorType },
        });
    }
    unregisterErrorHandler(errorType) {
        const removed = this.config.errorHandlers.delete(errorType);
        if (removed) {
            this.logger.debug('Error handler unregistered', {
                operation: 'error_handler_unregistration',
                metadata: { errorType },
            });
        }
        return removed;
    }
    async handleError(error, context = {}) {
        const mcpError = (0, MCPErrors_1.isMCPError)(error) ? error : MCPErrors_1.MCPErrorFactory.fromError(error);
        const fullContext = {
            correlationId: context.correlationId || this.logger.generateCorrelationId(),
            timestamp: new Date(),
            retryCount: 0,
            ...context,
        };
        this.logger.error('Error occurred', mcpError, {
            correlationId: fullContext.correlationId,
            ...(fullContext.method && { method: fullContext.method }),
            ...(fullContext.operation && { operation: fullContext.operation }),
            metadata: { retryCount: fullContext.retryCount },
        });
        if (this.config.enableCircuitBreaker && fullContext.operation) {
            const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
            if (!circuitBreaker.canExecute()) {
                const result = {
                    shouldRetry: false,
                    transformedError: MCPErrors_1.MCPErrorFactory.resourceLimit('circuit_breaker', 1, 0, fullContext.correlationId),
                    recoveryAction: 'circuit_breaker_open',
                };
                this.emit('error-handled', mcpError, fullContext, result);
                return result;
            }
        }
        const customHandler = this.config.errorHandlers.get(mcpError.constructor.name);
        if (customHandler) {
            try {
                const result = await customHandler(mcpError, fullContext, this.config.defaultRecoveryStrategy);
                this.emit('error-handled', mcpError, fullContext, result);
                return result;
            }
            catch (handlerError) {
                this.logger.error('Custom error handler failed', handlerError, {
                    correlationId: fullContext.correlationId,
                });
            }
        }
        const result = await this.defaultErrorHandling(mcpError, fullContext);
        if (this.config.enableCircuitBreaker && fullContext.operation) {
            const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
            circuitBreaker.recordResult(!result.shouldRetry || result.transformedError === undefined);
        }
        this.emit('error-handled', mcpError, fullContext, result);
        return result;
    }
    async executeWithErrorHandling(operation, context = {}) {
        const fullContext = {
            correlationId: context.correlationId || this.logger.generateCorrelationId(),
            timestamp: new Date(),
            retryCount: 0,
            ...context,
        };
        let lastError = null;
        const maxRetries = this.config.defaultRecoveryStrategy.maxRetries;
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                fullContext.retryCount = attempt;
                if (this.config.enableCircuitBreaker && fullContext.operation) {
                    const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
                    if (!circuitBreaker.canExecute()) {
                        throw MCPErrors_1.MCPErrorFactory.resourceLimit('circuit_breaker', 1, 0, fullContext.correlationId);
                    }
                }
                const result = await operation();
                if (this.config.enableCircuitBreaker && fullContext.operation) {
                    const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
                    circuitBreaker.recordResult(true);
                }
                return result;
            }
            catch (error) {
                lastError = (0, MCPErrors_1.isMCPError)(error) ? error : MCPErrors_1.MCPErrorFactory.fromError(error);
                if (this.config.enableCircuitBreaker && fullContext.operation) {
                    const circuitBreaker = this.getOrCreateCircuitBreaker(fullContext.operation);
                    circuitBreaker.recordResult(false);
                }
                const handlingResult = await this.handleError(lastError, fullContext);
                if (!handlingResult.shouldRetry || attempt >= maxRetries) {
                    throw handlingResult.transformedError || lastError;
                }
                if (handlingResult.retryAfterMs) {
                    await this.delay(handlingResult.retryAfterMs);
                }
                else {
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
    async defaultErrorHandling(error, context) {
        if (!(0, MCPErrors_1.isRecoverableError)(error)) {
            return {
                shouldRetry: false,
                transformedError: error,
                recoveryAction: 'no_recovery',
            };
        }
        if (context.retryCount >= this.config.defaultRecoveryStrategy.maxRetries) {
            return {
                shouldRetry: false,
                transformedError: error,
                recoveryAction: 'max_retries_exceeded',
            };
        }
        const isRetryable = this.config.defaultRecoveryStrategy.recoverableErrorTypes.includes(error.constructor.name);
        if (!isRetryable) {
            return {
                shouldRetry: false,
                transformedError: error,
                recoveryAction: 'error_type_not_retryable',
            };
        }
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
    calculateRetryDelay(attempt) {
        const { baseDelayMs, maxDelayMs, backoffMultiplier, jitterFactor } = this.config.defaultRecoveryStrategy;
        const delay = Math.min(baseDelayMs * Math.pow(backoffMultiplier, attempt), maxDelayMs);
        const jitter = delay * jitterFactor * Math.random();
        return Math.floor(delay + jitter);
    }
    getOrCreateCircuitBreaker(operation) {
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
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    getCircuitBreakerStatus(operation) {
        const circuitBreaker = this.circuitBreakers.get(operation);
        return circuitBreaker ? circuitBreaker.getStatus() : null;
    }
    resetCircuitBreaker(operation) {
        const circuitBreaker = this.circuitBreakers.get(operation);
        if (circuitBreaker) {
            circuitBreaker.reset();
            return true;
        }
        return false;
    }
    getStats() {
        const circuitBreakerStatuses = {};
        for (const [operation, breaker] of this.circuitBreakers.entries()) {
            circuitBreakerStatuses[operation] = breaker.getStatus();
        }
        return {
            activeCircuitBreakers: this.circuitBreakers.size,
            totalErrorHandlers: this.config.errorHandlers.size,
            circuitBreakerStatuses,
        };
    }
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.logger.info('Error middleware configuration updated', {
            operation: 'config_update',
        });
    }
    cleanup() {
        this.circuitBreakers.clear();
        this.retryAttempts.clear();
        this.removeAllListeners();
    }
    emit(event, ...args) {
        return super.emit(event, ...args);
    }
    on(event, listener) {
        return super.on(event, listener);
    }
    off(event, listener) {
        return super.off(event, listener);
    }
}
exports.ErrorMiddleware = ErrorMiddleware;
//# sourceMappingURL=ErrorMiddleware.js.map