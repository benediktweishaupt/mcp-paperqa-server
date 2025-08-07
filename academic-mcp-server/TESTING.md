# Testing Guide

This document outlines the testing strategy and infrastructure for the Academic MCP Server.

## Test Structure

The test suite is organized into multiple layers:

```
tests/
├── setup/                  # Global test configuration
│   ├── global-setup.ts     # Pre-test setup
│   └── global-teardown.ts  # Post-test cleanup
├── helpers/                # Test utilities
│   └── test-utils.ts       # Common test helpers
├── unit/                   # Unit tests (by module)
│   ├── tools/              # Tool system tests
│   ├── errors/             # Error handling tests
│   ├── logging/            # Logging system tests
│   ├── protocol/           # Protocol handler tests
│   └── middleware/         # Middleware tests
└── integration/            # Integration tests
    └── server.integration.test.ts
```

## Test Types

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Location**: `tests/{module}/*.test.ts`
- **Command**: `npm run test:unit`
- **Coverage Target**: 80%+ lines, functions, statements; 70%+ branches

### Integration Tests  
- **Purpose**: Test component interactions and full workflows
- **Location**: `tests/integration/*.test.ts`
- **Command**: `npm run test:integration`
- **Focus**: Server lifecycle, tool registration, protocol handling

### MCP Protocol Tests
- **Purpose**: Validate MCP protocol compliance
- **Location**: `scripts/test-mcp-integration.js`
- **Command**: `npm run test:mcp`
- **Focus**: Client-server communication, tool discovery, execution

## Running Tests

### Basic Commands

```bash
# Run all tests
npm test

# Run with coverage report
npm run test:coverage

# Run unit tests only
npm run test:unit

# Run integration tests only  
npm run test:integration

# Run MCP protocol tests
npm run test:mcp

# Watch mode for development
npm run test:watch

# CI mode (no watch, with coverage)
npm run test:ci
```

### Test Projects

The Jest configuration supports multiple test projects:

- **unit**: Runs unit tests with fast feedback
- **integration**: Runs integration tests with longer timeouts

## Test Utilities

### Test Helpers (`tests/helpers/test-utils.ts`)

Common utilities for test setup:

```typescript
import { createTestServer, createTestTool, createMockContext } from '../helpers/test-utils';

// Create test server instance
const server = createTestServer({ name: 'my-test-server' });

// Create mock tool for testing
const tool = createTestTool('test-tool', async () => ({ result: 'success' }));

// Create mock request context
const context = createMockContext({ requestId: 'test-123' });
```

### Assertion Helpers

Validate MCP-specific formats:

```typescript
import { assertions } from '../helpers/test-utils';

// Validate MCP response format
assertions.isValidMCPResponse(response);

// Validate tool metadata structure  
assertions.isValidToolMetadata(toolMeta);

// Validate error response format
assertions.isValidErrorResponse(errorResponse);
```

### Event Testing

Test asynchronous events:

```typescript
import { waitForEvent, waitForEvents } from '../helpers/test-utils';

// Wait for single event
const result = await waitForEvent(server, 'started', 5000);

// Wait for multiple events in sequence
const [started, ready] = await waitForEvents(server, ['started', 'ready']);
```

## Coverage Requirements

The test suite enforces minimum coverage thresholds:

- **Lines**: 80%
- **Functions**: 80%  
- **Statements**: 80%
- **Branches**: 70%

### Coverage Reports

Coverage reports are generated in multiple formats:

- **Console**: Summary displayed in terminal
- **HTML**: Detailed report in `coverage/` directory
- **LCOV**: Machine-readable format for CI/tooling

```bash
# Generate coverage report
npm run test:coverage

# Open HTML coverage report
open coverage/index.html
```

## Writing Tests

### Unit Test Example

```typescript
import { ToolValidator } from '../../src/tools/ToolValidator';
import { createTestTool } from '../helpers/test-utils';

describe('ToolValidator', () => {
  describe('validateRegistration', () => {
    it('should validate correct tool registration', () => {
      const tool = createTestTool('valid-tool');
      const result = ToolValidator.validateRegistration(tool);
      
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject invalid tool name', () => {
      const tool = createTestTool(''); // Invalid empty name
      const result = ToolValidator.validateRegistration(tool);
      
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Tool name is required');
    });
  });
});
```

### Integration Test Example

```typescript
import { AcademicMCPServer } from '../../src/server/AcademicMCPServer';
import { createTestServer, waitForEvent } from '../helpers/test-utils';

describe('Server Integration', () => {
  let server: AcademicMCPServer;

  beforeEach(() => {
    server = createTestServer();
  });

  afterEach(async () => {
    await server.stop();
  });

  it('should start and register tools', async () => {
    const startPromise = waitForEvent(server, 'started');
    
    await server.start();
    const startInfo = await startPromise;
    
    expect(startInfo).toMatchObject({
      name: expect.any(String),
      version: expect.any(String)
    });
    
    // Verify tools are registered
    const toolRegistry = (server as any).toolRegistry;
    const tools = toolRegistry.getAllToolsMetadata();
    expect(tools.length).toBeGreaterThan(0);
  });
});
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- **Pull Requests**: All test suites + coverage
- **Push to main**: Full test suite + integration tests
- **Release**: Extended test suite + MCP protocol validation

### Test Configuration for CI

```bash
# CI test command
npm run test:ci

# Environment variables for CI
NODE_ENV=test
LOG_LEVEL=error
CI=true
```

## Test Data and Fixtures

### Mock Data

Common test data is available in `test-utils.ts`:

```typescript
import { testData } from '../helpers/test-utils';

// Sample PDF content
const content = testData.samplePdfContent;

// Sample citations
const citation = testData.sampleCitation;

// Sample search response
const response = testData.sampleResponse;
```

### Temporary Files (Future)

When PDF processing is implemented:

```typescript
import { persistenceHelpers } from '../helpers/test-utils';

// Create temporary directory for tests
const tempDir = persistenceHelpers.createTempDirectory();

// Cleanup after tests
persistenceHelpers.cleanupTempFiles(tempDir);
```

## Performance Testing

### Test Timeouts

- **Unit Tests**: 5 seconds (default)
- **Integration Tests**: 10 seconds
- **MCP Protocol Tests**: 15 seconds

### Memory and Resource Testing

Integration tests monitor:
- Memory usage during server lifecycle
- Tool execution performance
- Connection handling under load

## Debugging Tests

### Running Single Tests

```bash
# Run specific test file
npm test -- tests/tools/ToolRegistry.test.ts

# Run tests matching pattern
npm test -- --testNamePattern="should register tool"

# Debug mode with verbose output
npm test -- --verbose --detectOpenHandles
```

### Test Environment Variables

```bash
# Enable debug logging in tests
LOG_LEVEL=debug npm test

# Run with Node debugger
node --inspect-brk node_modules/.bin/jest --runInBand
```

## Best Practices

### Test Organization
1. **Arrange-Act-Assert**: Clear test structure
2. **Descriptive Names**: Test names explain what is being tested
3. **Single Responsibility**: One concept per test
4. **Independent Tests**: No dependencies between tests

### Mocking Strategy
1. **External Dependencies**: Mock external services/APIs
2. **File System**: Mock file operations (when implemented)
3. **Time**: Mock dates/timers for deterministic tests
4. **Logging**: Mock loggers to reduce test noise

### Error Testing
1. **Happy Path**: Test successful operations
2. **Error Conditions**: Test expected failures
3. **Edge Cases**: Test boundary conditions
4. **Recovery**: Test error recovery mechanisms

## Future Testing Enhancements

As the project grows, additional testing will include:

### Phase 2: PDF Processing
- PDF parsing accuracy tests
- Document indexing performance tests  
- Search relevance scoring tests

### Phase 3: Advanced Features
- Citation extraction accuracy tests
- Argument tracking validation tests
- Research gap analysis tests

### Performance and Load Testing
- Tool execution under concurrent load
- Memory usage with large document sets
- Protocol handling with multiple clients

## Contributing to Tests

When adding new features:

1. **Write Tests First**: TDD approach preferred
2. **Maintain Coverage**: Keep above threshold requirements
3. **Update Documentation**: Add test examples to this guide
4. **Run Full Suite**: Ensure no regressions before submitting

### Test Review Checklist

- [ ] Unit tests cover new functionality
- [ ] Integration tests validate component interactions
- [ ] Error conditions are tested
- [ ] Coverage thresholds are maintained
- [ ] Tests are deterministic (no flaky tests)
- [ ] Test names clearly describe expectations