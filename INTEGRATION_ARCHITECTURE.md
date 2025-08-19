# PaperQA2 MCP Integration Architecture

**Date**: August 19, 2025  
**Task**: Design MCP Integration Architecture  
**Status**: Complete Design Specification  

## Overview

This document defines the architecture for integrating PaperQA2 (Python PyPI package) with our existing Academic MCP Server (TypeScript). The integration maintains clean separation between the MCP protocol layer and the academic research functionality.

## Current State Analysis

### Existing TypeScript MCP Server
- **Location**: `academic-mcp-server/`
- **Framework**: Full-featured MCP server with tool registry
- **Components**: Protocol handlers, streaming, routing, error handling
- **Status**: Production-ready foundation

### PaperQA2 Integration Target
- **Package**: `paper-qa` from PyPI (v5.28.0)
- **Capabilities**: Academic research, embeddings, agent workflows
- **Dependencies**: Voyage AI, Gemini, OpenAI embeddings supported
- **Status**: Validated and working

## Integration Architecture Design

### 1. Bridge Architecture Pattern

We use a **Bridge Pattern** to separate the MCP interface from PaperQA2 implementation:

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────▼───────────────────────────────────────┐
│              TypeScript MCP Server                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐│
│  │   Tool Registry │ │ Protocol Handler│ │ Stream Handler ││
│  └─────────────────┘ └─────────────────┘ └────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │ Python Bridge
┌─────────────────────▼───────────────────────────────────────┐
│                Python Bridge Process                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐│
│  │ PaperQA2 Wrapper│ │   Configuration │ │  Error Handler ││
│  └─────────────────┘ └─────────────────┘ └────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │ Python Imports
┌─────────────────────▼───────────────────────────────────────┐
│                   PaperQA2 Package                         │
│         paperqa.Docs, paperqa.Settings, agent_query        │
└─────────────────────────────────────────────────────────────┘
```

### 2. Component Architecture

#### 2.1 TypeScript MCP Tools (New)

Create PaperQA2-specific tools in the existing tool registry:

**File**: `academic-mcp-server/src/tools/paperqa/`

- `LiteratureSearchTool.ts` - Academic literature search
- `DocumentUploadTool.ts` - PDF document management  
- `LibraryStatusTool.ts` - Research library information
- `EmbeddingConfigTool.ts` - Embedding model configuration
- `CitationTool.ts` - Citation generation and formatting

#### 2.2 Python Bridge Service (New)

**File**: `paperqa_bridge.py` (root level)

A standalone Python service that:
- Exposes PaperQA2 functionality via HTTP/JSON API
- Handles PaperQA2 Settings and Docs management
- Manages paper directory and embeddings
- Provides structured error responses

#### 2.3 Integration Configuration (New)

**File**: `academic-mcp-server/src/config/PaperQAConfig.ts`

Configuration bridge between MCP and PaperQA2:
- Embedding model selection (Voyage AI, Gemini, OpenAI)
- Paper directory management
- API key configuration
- Performance settings

### 3. Communication Protocol

#### 3.1 TypeScript → Python Communication

**Method**: HTTP/JSON API (local subprocess)

**Rationale**: 
- Clean separation between TypeScript and Python
- Structured error handling
- Async-friendly for both sides
- Easy to test and debug
- No complex serialization issues

**API Endpoints**:
```typescript
POST /search-literature
POST /add-document  
GET  /library-status
POST /configure-embedding
POST /get-citation
GET  /health
```

#### 3.2 Process Management

**Startup Sequence**:
1. TypeScript MCP server starts
2. Spawns Python bridge process (`python paperqa_bridge.py`)
3. Waits for Python bridge health check
4. Registers PaperQA2 tools with MCP tool registry
5. Ready to serve Claude Desktop

**Error Handling**:
- Python process crash → restart automatically
- API timeouts → graceful degradation
- Invalid responses → structured error messages

### 4. Detailed Component Design

#### 4.1 PaperQA2 Bridge Service (`paperqa_bridge.py`)

```python
"""
PaperQA2 Bridge Service
Exposes PaperQA2 functionality via HTTP API for MCP integration
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from paperqa import Docs, Settings, agent_query
from pathlib import Path
import asyncio
import uvicorn

app = FastAPI(title="PaperQA2 Bridge", version="1.0.0")

class BridgeConfig:
    def __init__(self):
        self.settings = Settings(
            embedding="voyage-ai/voyage-3-lite",
            llm="gpt-4o-2024-11-20", 
            temperature=0.0
        )
        self.docs = Docs()
        self.paper_directory = Path("papers")
        self.paper_directory.mkdir(exist_ok=True)

config = BridgeConfig()

@app.post("/search-literature")
async def search_literature(request: SearchRequest):
    try:
        response = await agent_query(
            query=request.query,
            settings=config.settings,
            docs=config.docs
        )
        return {
            "answer": response.session.answer,
            "cost": response.session.cost,
            "sources": len(response.session.contexts)
        }
    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)}")

@app.post("/add-document") 
async def add_document(request: UploadRequest):
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(404, f"File not found: {file_path}")
            
        with open(file_path, 'rb') as f:
            await config.docs.aadd_file(
                file=f,
                docname=request.document_name or file_path.stem,
                settings=config.settings
            )
        
        return {"status": "success", "document_count": len(config.docs.docs)}
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "paperqa_version": paperqa.__version__}
```

#### 4.2 TypeScript Literature Search Tool

```typescript
// academic-mcp-server/src/tools/paperqa/LiteratureSearchTool.ts

import { ToolHandler, ToolRegistration, ToolContext } from '../types';
import { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { PaperQABridge } from '../../services/PaperQABridge';

export const literatureSearchTool: ToolRegistration = {
  metadata: {
    name: 'search_literature',
    description: 'Search academic literature using PaperQA2 agent workflow',
    version: '1.0.0',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Research question or topic to search for',
          minLength: 5,
          maxLength: 500
        },
        max_results: {
          type: 'number',
          description: 'Maximum number of results (1-20)',
          minimum: 1,
          maximum: 20
        },
        min_year: {
          type: 'number', 
          description: 'Earliest publication year',
          minimum: 1900
        },
        max_year: {
          type: 'number',
          description: 'Latest publication year', 
          maximum: 2030
        }
      },
      required: ['query']
    },
    category: 'academic',
    tags: ['research', 'literature', 'search', 'paperqa']
  },

  handler: async (args: Record<string, unknown>, context: ToolContext): Promise<CallToolResult> => {
    try {
      const { query, max_results = 5, min_year, max_year } = args;

      const bridge = PaperQABridge.getInstance();
      const result = await bridge.searchLiterature({
        query: query as string,
        max_results: max_results as number,
        min_year: min_year as number,
        max_year: max_year as number
      });

      return {
        content: [
          {
            type: 'text',
            text: `# Literature Search Results\n\n${result.answer}\n\n**Sources**: ${result.sources} | **Cost**: $${result.cost.toFixed(4)}`
          }
        ],
        isError: false
      };

    } catch (error) {
      return {
        content: [
          {
            type: 'text', 
            text: `Literature search failed: ${error instanceof Error ? error.message : String(error)}`
          }
        ],
        isError: true
      };
    }
  }
};
```

#### 4.3 PaperQA Bridge Client (`PaperQABridge.ts`)

```typescript
// academic-mcp-server/src/services/PaperQABridge.ts

import { spawn, ChildProcess } from 'child_process';
import axios, { AxiosInstance } from 'axios';

export interface SearchRequest {
  query: string;
  max_results?: number;
  min_year?: number;
  max_year?: number;
}

export interface SearchResponse {
  answer: string;
  cost: number;
  sources: number;
}

export class PaperQABridge {
  private static instance: PaperQABridge;
  private pythonProcess: ChildProcess | null = null;
  private client: AxiosInstance;
  private isReady = false;

  private constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8001',
      timeout: 30000
    });
  }

  static getInstance(): PaperQABridge {
    if (!PaperQABridge.instance) {
      PaperQABridge.instance = new PaperQABridge();
    }
    return PaperQABridge.instance;
  }

  async start(): Promise<void> {
    if (this.isReady) return;

    // Start Python bridge process
    this.pythonProcess = spawn('python3', ['paperqa_bridge.py'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env }
    });

    // Wait for health check
    await this.waitForReady();
    this.isReady = true;
  }

  private async waitForReady(maxAttempts = 10): Promise<void> {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        await this.client.get('/health');
        return;
      } catch {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    throw new Error('PaperQA bridge failed to start');
  }

  async searchLiterature(request: SearchRequest): Promise<SearchResponse> {
    const response = await this.client.post('/search-literature', request);
    return response.data;
  }

  async addDocument(filePath: string, documentName?: string): Promise<{status: string, document_count: number}> {
    const response = await this.client.post('/add-document', {
      file_path: filePath,
      document_name: documentName
    });
    return response.data;
  }

  async getLibraryStatus(): Promise<{document_count: number, status: string}> {
    const response = await this.client.get('/library-status');
    return response.data;
  }

  async stop(): Promise<void> {
    if (this.pythonProcess) {
      this.pythonProcess.kill('SIGTERM');
      this.pythonProcess = null;
    }
    this.isReady = false;
  }
}
```

### 5. Configuration Management

#### 5.1 Environment Variables

```bash
# PaperQA2 Configuration
PAPERQA_EMBEDDING_MODEL=voyage-ai/voyage-3-lite
PAPERQA_LLM_MODEL=gpt-4o-2024-11-20
PAPERQA_PAPER_DIRECTORY=./papers
PAPERQA_BRIDGE_PORT=8001

# API Keys (for PaperQA2)
OPENAI_API_KEY=your-openai-key
VOYAGE_API_KEY=your-voyage-key
GEMINI_API_KEY=your-gemini-key
```

#### 5.2 MCP Configuration Bridge

```typescript
// academic-mcp-server/src/config/PaperQAConfig.ts

export interface PaperQAConfig {
  embeddingModel: 'voyage-ai/voyage-3-lite' | 'gemini/gemini-embedding-001' | 'text-embedding-3-small';
  llmModel: string;
  paperDirectory: string;
  bridgePort: number;
  maxConcurrentRequests: number;
  evidenceK: number;
}

export const defaultPaperQAConfig: PaperQAConfig = {
  embeddingModel: 'voyage-ai/voyage-3-lite',
  llmModel: 'gpt-4o-2024-11-20',
  paperDirectory: './papers',
  bridgePort: 8001,
  maxConcurrentRequests: 2,
  evidenceK: 8
};
```

### 6. Error Handling Strategy

#### 6.1 Error Categories

1. **Python Process Errors**: Bridge process crashes/fails to start
2. **API Communication Errors**: HTTP timeouts, connection failures
3. **PaperQA2 Errors**: Invalid documents, API key issues, rate limits
4. **Configuration Errors**: Missing environment variables, invalid settings

#### 6.2 Error Recovery

```typescript
// Automatic retry logic
async function withRetry<T>(operation: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
  throw new Error('Max retries exceeded');
}

// Process restart logic  
async function ensureBridgeRunning(): Promise<void> {
  const bridge = PaperQABridge.getInstance();
  try {
    await bridge.client.get('/health');
  } catch {
    console.warn('PaperQA bridge unhealthy, restarting...');
    await bridge.stop();
    await bridge.start();
  }
}
```

### 7. Integration Points

#### 7.1 MCP Server Startup Integration

```typescript
// academic-mcp-server/src/index.ts - Modified startup

import { PaperQABridge } from './services/PaperQABridge';
import { registerPaperQATools } from './tools/paperqa';

async function startServer() {
  // Start PaperQA Bridge
  const bridge = PaperQABridge.getInstance();
  await bridge.start();

  // Create MCP Server
  const server = new AcademicMCPServer({
    name: 'academic-mcp-server',
    version: '1.0.0',
    description: 'Academic research MCP server with PaperQA2 integration'
  });

  // Register PaperQA2 tools
  await registerPaperQATools(server);

  // Start MCP server
  await server.start();

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    await server.stop();
    await bridge.stop();
  });
}
```

#### 7.2 Tool Registration

```typescript
// academic-mcp-server/src/tools/paperqa/index.ts

import { AcademicMCPServer } from '../../server/AcademicMCPServer';
import { literatureSearchTool } from './LiteratureSearchTool';
import { documentUploadTool } from './DocumentUploadTool';
import { libraryStatusTool } from './LibraryStatusTool';
import { embeddingConfigTool } from './EmbeddingConfigTool';

export async function registerPaperQATools(server: AcademicMCPServer): Promise<void> {
  await server.registerTool(literatureSearchTool);
  await server.registerTool(documentUploadTool);
  await server.registerTool(libraryStatusTool);
  await server.registerTool(embeddingConfigTool);
}
```

## Implementation Timeline

### Phase 1: Core Bridge (Day 1)
1. Create `paperqa_bridge.py` with basic FastAPI endpoints
2. Create `PaperQABridge.ts` TypeScript client
3. Test basic communication

### Phase 2: Tool Implementation (Day 2) 
1. Implement `LiteratureSearchTool.ts`
2. Implement `DocumentUploadTool.ts` 
3. Add error handling and recovery

### Phase 3: Integration & Testing (Day 3)
1. Integrate with existing MCP server startup
2. Add configuration management
3. End-to-end testing with Claude Desktop

## Success Criteria

- ✅ TypeScript MCP server can spawn and communicate with Python bridge
- ✅ Literature search works through Claude Desktop
- ✅ Document upload and management functional
- ✅ Error handling gracefully manages Python process issues
- ✅ Configuration allows switching embedding models
- ✅ Performance meets targets (<15s response time, <4GB memory)

## Conclusion

This architecture provides a clean separation between the MCP protocol layer (TypeScript) and the academic research functionality (PaperQA2/Python), while maintaining high performance and reliability. The bridge pattern allows for easy testing, debugging, and future enhancements without disrupting either side of the integration.

---

**Status**: Design Complete ✅  
**Next Task**: Implementation Phase 1 - Core Bridge Development