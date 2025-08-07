# Academic MCP Server

MCP server for academic research assistance with PDF processing and intelligent search capabilities.

## Features

- Intelligent literature search across academic PDFs
- Semantic text chunking that preserves argumentative flow
- Academic-optimized embedding generation
- Source attribution with exact page/paragraph references
- Citation management with multiple format support

## Installation

```bash
npm install
```

## Development

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run in development mode with hot reload
npm run dev

# Run tests
npm test

# Run linting
npm run lint

# Format code
npm run format
```

## Architecture

This MCP server provides tools for:
- Literature search with context preservation
- Document retrieval and processing
- Citation lookup and formatting
- Source attribution tracking

## Project Structure

```
src/
├── index.ts          # Main server entry point
├── server/           # MCP server implementation (TODO)
├── tools/            # MCP tool implementations (TODO)
├── processing/       # PDF processing engine (TODO)
├── search/           # Search and embedding system (TODO)
└── citation/         # Citation management system (TODO)

tests/
├── setup.ts          # Test configuration
└── *.test.ts         # Test files
```

## Development Status

✅ Phase 1: MCP Server Foundation Setup
- [x] TypeScript project initialization
- [ ] MCP server class implementation
- [ ] Tool registration framework
- [ ] Communication protocol setup
- [ ] Error handling and logging
- [ ] Claude Desktop integration
- [ ] Testing infrastructure

🔄 Phase 2: Academic PDF Processing (Pending)
🔄 Phase 3: Intelligent Text Chunking (Pending)
🔄 Phase 4: Embedding Generation (Pending)
🔄 Phase 5: Search Implementation (Pending)

## License

MIT