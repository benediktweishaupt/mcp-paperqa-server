// Error classes
export {
  MCPError,
  ProtocolError,
  ValidationError,
  ToolError,
  NotFoundError,
  RateLimitError,
  AuthenticationError,
  TimeoutError,
  ConfigurationError,
  ResourceLimitError,
  InternalServerError,
  DependencyError,
  MCPErrorFactory,
  ErrorCodes,
  isMCPError,
  isRecoverableError,
} from './MCPErrors';