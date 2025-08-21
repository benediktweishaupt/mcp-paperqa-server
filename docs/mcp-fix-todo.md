# MCP Server Fix - TODO List

**Branch:** `fix/mcp-async-taskgroup-errors`  
**Goal:** Fix FastMCP TaskGroup async errors to enable seamless Claude Code → PaperQA integration

## Current Problem
- ✅ **PaperQA core works perfectly** (direct Python API)
- ❌ **MCP wrapper fails** with "unhandled errors in a TaskGroup (1 sub-exception)"
- **Root cause**: FastMCP async race condition, likely from concurrent progress reporting

## TODO List

### Phase 1: Minimal MCP Server (1 hour)
- [ ] **Strip down MCP server to bare minimum**
  - Remove all progress reporting (`ctx.report_progress`)
  - Remove concurrent operations
  - Single simple search_literature function only
  - Test if basic query works without TaskGroup errors

- [ ] **Create minimal test version**
  - Copy `server.py` to `server_minimal.py`
  - Remove FastMCP Context usage
  - Simple request → response pattern
  - Test with single MCP call

- [ ] **Debug async patterns**
  - Check if FastMCP Context is thread-safe
  - Verify agent_query is properly awaited
  - Look for any concurrent async operations

### Phase 2: Incremental Restoration (30 min)
- [ ] **Add back features one by one**
  - Basic error handling
  - Simple status messages (no progress bars)
  - Parameter validation
  - Test each addition individually

- [ ] **Identify problematic pattern**
  - Which specific code causes TaskGroup error?
  - Progress reporting? Multiple async calls? Context usage?
  - Document the exact failure point

### Phase 3: Robust Implementation (30 min)  
- [ ] **Fix the async issue properly**
  - Use proper async/await patterns
  - Avoid concurrent Context operations
  - Single-threaded progress updates if needed

- [ ] **Add comprehensive error handling**
  - Catch TaskGroup exceptions specifically
  - Provide meaningful error messages
  - Graceful degradation if needed

- [ ] **Test integration thoroughly**
  - Multiple concurrent requests
  - Different query types
  - Error scenarios

### Phase 4: Production Ready (15 min)
- [ ] **Restore full functionality**
  - Progress reporting (if compatible)
  - All tool parameters
  - Complete error handling
  - User-friendly responses

- [ ] **Documentation**
  - Update debugging report
  - Document the fix
  - Add troubleshooting guide

## Investigation Areas

### Suspected Root Causes
1. **Progress reporting race condition**
   - Multiple `ctx.report_progress()` calls concurrent with main query
   - FastMCP Context not thread-safe
   
2. **Agent query async pattern**
   - `agent_query()` creates internal TaskGroups
   - Conflict with FastMCP's async handling
   
3. **Settings object mutation**
   - Multiple references to same settings object
   - Concurrent modifications causing issues

### Files to Focus On
- `paperqa-mcp/server.py` (line 100-150) - Main search function
- FastMCP documentation - Proper Context usage patterns
- PaperQA2 async patterns - How agent_query should be called

### Quick Wins to Try
- [ ] Remove all `ctx.report_progress()` calls
- [ ] Remove all `await ctx.info()` calls  
- [ ] Use basic string return instead of formatted response
- [ ] Test with minimal async function

## Success Criteria
- [ ] MCP call returns successful response (not TaskGroup error)
- [ ] Answer quality matches direct PaperQA API
- [ ] Can handle multiple sequential requests
- [ ] Error handling provides useful feedback

## Time Estimate
- **Phase 1**: 1 hour (minimal working version)
- **Phase 2**: 30 min (incremental testing)
- **Phase 3**: 30 min (proper fix)  
- **Phase 4**: 15 min (polish)
- **Total**: ~2.5 hours maximum

## Backup Plan
If FastMCP proves too problematic:
- [ ] Switch to basic MCP server implementation
- [ ] Manual JSON-RPC handling
- [ ] Simpler async patterns with more control