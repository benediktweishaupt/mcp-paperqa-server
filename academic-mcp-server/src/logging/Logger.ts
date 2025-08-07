import winston, { Logger as WinstonLogger, transports, format } from 'winston';
import { v4 as uuidv4 } from 'uuid';
import { MCPError } from '../errors/MCPErrors';

/**
 * Log level definitions
 */
export type LogLevel = 'error' | 'warn' | 'info' | 'debug';

/**
 * Log context for correlation and structured logging
 */
export interface LogContext {
  correlationId?: string;
  requestId?: string;
  toolName?: string;
  method?: string;
  userId?: string;
  sessionId?: string;
  operation?: string;
  duration?: number;
  metadata?: Record<string, unknown>;
}

/**
 * Performance metrics for logging
 */
export interface PerformanceMetrics {
  operation: string;
  duration: number;
  startTime: Date;
  endTime: Date;
  success: boolean;
  errorType?: string;
  memoryUsage?: {
    heapUsed: number;
    heapTotal: number;
    external: number;
    rss: number;
  };
}

/**
 * Logger configuration
 */
export interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableFile: boolean;
  fileOptions?: {
    filename: string;
    maxsize: number;
    maxFiles: number;
  };
  enableStructuredLogging: boolean;
  enablePerformanceLogging: boolean;
  enableRequestLogging: boolean;
  correlationIdHeader?: string;
  sensitiveFields: string[];
}

/**
 * MCP Logger Class
 * Provides structured logging with correlation IDs and performance metrics
 */
export class MCPLogger {
  private logger: WinstonLogger;
  private config: LoggerConfig;
  private performanceTracker = new Map<string, { startTime: Date; operation: string; context?: LogContext | undefined }>();

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: 'info',
      enableConsole: true,
      enableFile: false,
      enableStructuredLogging: true,
      enablePerformanceLogging: true,
      enableRequestLogging: true,
      correlationIdHeader: 'x-correlation-id',
      sensitiveFields: ['password', 'token', 'secret', 'key', 'authorization'],
      ...config,
    };

    this.logger = this.createWinstonLogger();
  }

  /**
   * Create Winston logger instance
   */
  private createWinstonLogger(): WinstonLogger {
    const logFormat = this.config.enableStructuredLogging
      ? this.createStructuredFormat()
      : format.simple();

    const logTransports: winston.transport[] = [];

    // Console transport
    if (this.config.enableConsole) {
      logTransports.push(
        new transports.Console({
          format: format.combine(
            format.colorize(),
            format.timestamp(),
            logFormat
          ),
        })
      );
    }

    // File transport
    if (this.config.enableFile && this.config.fileOptions) {
      logTransports.push(
        new transports.File({
          ...this.config.fileOptions,
          format: format.combine(
            format.timestamp(),
            logFormat
          ),
        })
      );
    }

    return winston.createLogger({
      level: this.config.level,
      transports: logTransports,
      exitOnError: false,
      // Handle uncaught exceptions and rejections
      exceptionHandlers: this.config.enableFile && this.config.fileOptions
        ? [
          new transports.File({
            filename: this.config.fileOptions.filename.replace('.log', '-exceptions.log'),
          }),
        ]
        : [],
      rejectionHandlers: this.config.enableFile && this.config.fileOptions
        ? [
          new transports.File({
            filename: this.config.fileOptions.filename.replace('.log', '-rejections.log'),
          }),
        ]
        : [],
    });
  }

  /**
   * Create structured log format
   */
  private createStructuredFormat() {
    return format.printf((info) => {
      const { timestamp, level, message, ...meta } = info;
      
      const logEntry: Record<string, unknown> = {
        timestamp,
        level: level.toUpperCase(),
        message,
        ...this.sanitizeLogData(meta),
      };

      return JSON.stringify(logEntry);
    });
  }

  /**
   * Sanitize log data to remove sensitive information
   */
  private sanitizeLogData(data: Record<string, unknown>): Record<string, unknown> {
    const sanitized = { ...data };

    for (const field of this.config.sensitiveFields) {
      if (field in sanitized) {
        sanitized[field] = '[REDACTED]';
      }
    }

    // Recursively sanitize nested objects
    for (const [key, value] of Object.entries(sanitized)) {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        sanitized[key] = this.sanitizeLogData(value as Record<string, unknown>);
      }
    }

    return sanitized;
  }

  /**
   * Generate correlation ID
   */
  generateCorrelationId(): string {
    return `mcp-${uuidv4()}`;
  }

  /**
   * Log error with context
   */
  error(message: string, error?: Error | MCPError, context?: LogContext): void {
    const logData: Record<string, unknown> = {
      ...context,
      message,
    };

    if (error) {
      if (error instanceof MCPError) {
        logData.error = error.toLogFormat();
      } else {
        logData.error = {
          name: error.name,
          message: error.message,
          stack: error.stack,
        };
      }
    }

    this.logger.error(logData);
  }

  /**
   * Log warning with context
   */
  warn(message: string, context?: LogContext): void {
    this.logger.warn({
      message,
      ...context,
    });
  }

  /**
   * Log info with context
   */
  info(message: string, context?: LogContext): void {
    this.logger.info({
      message,
      ...context,
    });
  }

  /**
   * Log debug with context
   */
  debug(message: string, context?: LogContext): void {
    this.logger.debug({
      message,
      ...context,
    });
  }

  /**
   * Log request start
   */
  logRequestStart(method: string, correlationId: string, params?: unknown): void {
    if (!this.config.enableRequestLogging) return;

    this.info('Request started', {
      correlationId,
      method,
      operation: 'request_start',
      metadata: { params: this.sanitizeLogData({ params }) },
    });
  }

  /**
   * Log request completion
   */
  logRequestEnd(
    method: string,
    correlationId: string,
    success: boolean,
    duration: number,
    result?: unknown,
    error?: Error
  ): void {
    if (!this.config.enableRequestLogging) return;

    const logData: LogContext = {
      correlationId,
      method,
      operation: 'request_end',
      duration,
      metadata: {
        success,
        result: success ? this.sanitizeLogData({ result }) : undefined,
      },
    };

    if (success) {
      this.info('Request completed successfully', logData);
    } else {
      this.error('Request failed', error, logData);
    }
  }

  /**
   * Start performance tracking
   */
  startPerformanceTracking(operation: string, context?: LogContext): string {
    if (!this.config.enablePerformanceLogging) return '';

    const trackingId = uuidv4();
    this.performanceTracker.set(trackingId, {
      startTime: new Date(),
      operation,
      context: context as LogContext | undefined,
    });

    this.debug('Performance tracking started', {
      ...context,
      operation,
      metadata: { ...context?.metadata, trackingId },
    });

    return trackingId;
  }

  /**
   * End performance tracking and log metrics
   */
  endPerformanceTracking(
    trackingId: string,
    success: boolean = true,
    error?: Error,
    additionalMetrics?: Record<string, unknown>
  ): PerformanceMetrics | null {
    if (!this.config.enablePerformanceLogging) return null;

    const tracking = this.performanceTracker.get(trackingId);
    if (!tracking) {
      this.warn('Performance tracking not found', { 
        metadata: { trackingId }
      });
      return null;
    }

    this.performanceTracker.delete(trackingId);

    const endTime = new Date();
    const duration = endTime.getTime() - tracking.startTime.getTime();

    const metrics = {
      operation: tracking.operation,
      duration,
      startTime: tracking.startTime,
      endTime,
      success,
      errorType: error?.name,
      memoryUsage: process.memoryUsage(),
    } as PerformanceMetrics;

    const logContext: LogContext = {
      ...tracking.context,
      operation: 'performance_metrics',
      duration,
      metadata: {
        ...additionalMetrics,
        metrics,
      },
    };

    if (success) {
      this.info(`Performance: ${tracking.operation} completed in ${duration}ms`, logContext);
    } else {
      this.warn(`Performance: ${tracking.operation} failed after ${duration}ms`, logContext);
    }

    return metrics;
  }

  /**
   * Log tool execution
   */
  logToolExecution(
    toolName: string,
    operation: string,
    success: boolean,
    duration: number,
    correlationId?: string,
    error?: Error,
    args?: Record<string, unknown>
  ): void {
    const context = {
      correlationId,
      toolName,
      operation,
      duration,
      metadata: {
        success,
        arguments: this.sanitizeLogData(args || {}),
      },
    } as LogContext;

    if (success) {
      this.info(`Tool execution: ${toolName}.${operation} completed`, context);
    } else {
      this.error(`Tool execution: ${toolName}.${operation} failed`, error, context);
    }
  }

  /**
   * Log server events
   */
  logServerEvent(event: string, data?: Record<string, unknown>): void {
    this.info(`Server event: ${event}`, {
      operation: 'server_event',
      metadata: this.sanitizeLogData(data || {}),
    });
  }

  /**
   * Log protocol events
   */
  logProtocolEvent(
    event: string,
    correlationId?: string,
    data?: Record<string, unknown>
  ): void {
    this.info(`Protocol event: ${event}`, {
      correlationId,
      operation: 'protocol_event',
      metadata: this.sanitizeLogData(data || {}),
    } as LogContext);
  }

  /**
   * Create child logger with additional context
   */
  child(defaultContext: LogContext): MCPLogger {
    const childLogger = new MCPLogger(this.config);
    
    // Override logging methods to include default context
    const originalError = childLogger.error.bind(childLogger);
    const originalWarn = childLogger.warn.bind(childLogger);
    const originalInfo = childLogger.info.bind(childLogger);
    const originalDebug = childLogger.debug.bind(childLogger);

    childLogger.error = (message: string, error?: Error | MCPError, context?: LogContext) => {
      return originalError(message, error, { ...defaultContext, ...context });
    };

    childLogger.warn = (message: string, context?: LogContext) => {
      return originalWarn(message, { ...defaultContext, ...context });
    };

    childLogger.info = (message: string, context?: LogContext) => {
      return originalInfo(message, { ...defaultContext, ...context });
    };

    childLogger.debug = (message: string, context?: LogContext) => {
      return originalDebug(message, { ...defaultContext, ...context });
    };

    return childLogger;
  }

  /**
   * Set log level dynamically
   */
  setLogLevel(level: LogLevel): void {
    this.config.level = level;
    this.logger.level = level;
  }

  /**
   * Get current configuration
   */
  getConfig(): Readonly<LoggerConfig> {
    return { ...this.config };
  }

  /**
   * Get logger statistics
   */
  getStats(): {
    activePerformanceTracking: number;
    logLevel: string;
    transportsCount: number;
  } {
    return {
      activePerformanceTracking: this.performanceTracker.size,
      logLevel: this.logger.level,
      transportsCount: this.logger.transports.length,
    };
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.performanceTracker.clear();
    this.logger.close();
  }
}