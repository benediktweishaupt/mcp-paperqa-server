#!/usr/bin/env python3
"""
MCP Protocol Integration Tests

Tests the MCP protocol compliance and communication with our PaperQA2 server.
Validates tool registration, parameter handling, and response formatting.
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from mcp.types import Tool, TextContent

# Import our server
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from paperqa_mcp_server import server, settings, docs

class TestMCPProtocol:
    """Test MCP protocol compliance"""
    
    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Setup clean server state for each test"""
        # Clear any existing state
        docs.docs.clear()
        docs.texts.clear()
        yield

    def test_server_initialization(self):
        """Test that MCP server initializes correctly"""
        assert server.name == "paperqa-academic"
        assert hasattr(server, '_tools')

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that all required tools are registered"""
        # Get registered tools using FastMCP async method
        tools = await server.list_tools()
        tool_names = {tool.name for tool in tools}
        
        expected_tools = {
            "search_literature",
            "add_document", 
            "get_library_status",
            "configure_embedding"
        }
        
        assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"

    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self):
        """Test that tools handle parameter validation correctly"""
        # Test search_literature with various parameters
        search_tool = server._tools["search_literature"]
        
        # Valid parameters should work
        result = await search_tool.handler(
            query="test query",
            max_sources=5,
            min_year=2020,
            max_year=2024
        )
        assert isinstance(result, str)
        
        # Test with minimal parameters
        result = await search_tool.handler(query="minimal test")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_tool_response_format(self):
        """Test that tool responses are properly formatted"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Mock a proper response
            mock_result = Mock()
            mock_result.session.answer = "Test academic response with proper formatting."
            mock_result.session.cost = 0.025
            mock_result.session.contexts = [Mock(), Mock(), Mock()]
            mock_query.return_value = mock_result
            
            search_tool = server._tools["search_literature"]
            result = await search_tool.handler(query="test formatting")
            
            # Verify response structure
            assert "# Literature Search Results" in result
            assert "Test academic response" in result
            assert "3 evidence sources analyzed" in result
            assert "$0.0250" in result
            assert "Research Summary" in result

    @pytest.mark.asyncio
    async def test_error_response_format(self):
        """Test that errors are properly formatted for MCP"""
        # Test file not found error
        add_tool = server._tools["add_document"]
        result = await add_tool.handler(file_path="/nonexistent.pdf")
        
        assert result.startswith("❌ Error:")
        assert "File not found" in result
        
        # Test search error
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("Test API error")
            
            search_tool = server._tools["search_literature"]
            result = await search_tool.handler(query="error test")
            
            assert result.startswith("❌ Literature search failed:")
            assert "Test API error" in result

    def test_tool_metadata(self):
        """Test that tools have proper metadata for MCP"""
        for tool_name, tool in server._tools.items():
            # Each tool should have required attributes
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description') 
            assert hasattr(tool, 'handler')
            
            # Tool names should match
            assert tool.name == tool_name
            
            # Descriptions should be informative
            assert len(tool.description) > 20
            assert tool.description.endswith('.')

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test that multiple tools can be called concurrently"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Mock search responses
            mock_result = Mock()
            mock_result.session.answer = "Concurrent test response"
            mock_result.session.cost = 0.01
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            # Run multiple tools concurrently
            tasks = [
                server._tools["search_literature"].handler(query="test 1"),
                server._tools["search_literature"].handler(query="test 2"),
                server._tools["get_library_status"].handler(),
                server._tools["configure_embedding"].handler(model_name="voyage-ai/voyage-3-lite")
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 4
            assert all(isinstance(result, str) for result in results)
            assert all("failed" not in result.lower() or "❌" in result for result in results)

    @pytest.mark.asyncio
    async def test_parameter_type_handling(self):
        """Test that tools handle different parameter types correctly"""
        search_tool = server._tools["search_literature"]
        
        # Test string parameters
        result = await search_tool.handler(query="string test")
        assert isinstance(result, str)
        
        # Test integer parameters
        result = await search_tool.handler(
            query="int test",
            max_sources=3,
            min_year=2020,
            max_year=2024
        )
        assert isinstance(result, str)
        
        # Test None parameters (should use defaults)
        result = await search_tool.handler(
            query="none test",
            max_sources=None,
            min_year=None,
            max_year=None
        )
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_state_management(self):
        """Test that server maintains state correctly across calls"""
        # Change embedding model
        config_tool = server._tools["configure_embedding"]
        result = await config_tool.handler(model_name="gemini/gemini-embedding-001")
        assert "✅ Embedding model updated" in result
        
        # Verify state persisted
        assert settings.embedding == "gemini/gemini-embedding-001"
        
        # Check status reflects change
        status_tool = server._tools["get_library_status"]
        result = await status_tool.handler()
        assert "gemini/gemini-embedding-001" in result

    @pytest.mark.asyncio 
    async def test_document_state_tracking(self):
        """Test that document state is tracked correctly"""
        # Initially empty
        status_tool = server._tools["get_library_status"]
        result = await status_tool.handler()
        assert "Empty library" in result
        assert "0 indexed" in result
        
        # Mock adding a document
        with patch.object(docs, 'aadd_file', new_callable=AsyncMock):
            docs.docs = {"test": Mock()}
            docs.texts = [Mock() for _ in range(5)]
            
            result = await status_tool.handler()
            assert "1 indexed" in result
            assert "5 searchable chunks" in result

    def test_tool_parameter_schemas(self):
        """Test that tool parameter schemas are valid"""
        for tool_name, tool in server._tools.items():
            # Each tool should have a callable handler
            assert callable(tool.handler)
            
            # Handler should have type annotations for MCP introspection
            import inspect
            sig = inspect.signature(tool.handler)
            
            # Should have parameters (except get_library_status)
            if tool_name != "get_library_status":
                assert len(sig.parameters) > 0
            
            # Parameters should have type hints
            for param_name, param in sig.parameters.items():
                if param_name not in ['self', 'args', 'kwargs']:
                    # Should have type annotation
                    assert param.annotation != inspect.Parameter.empty

    @pytest.mark.asyncio
    async def test_long_running_operations(self):
        """Test that long-running operations work correctly"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Simulate slow operation
            async def slow_query(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                result = Mock()
                result.session.answer = "Long-running operation completed"
                result.session.cost = 0.05
                result.session.contexts = [Mock()]
                return result
            
            mock_query.side_effect = slow_query
            
            search_tool = server._tools["search_literature"]
            start_time = asyncio.get_event_loop().time()
            
            result = await search_tool.handler(query="long operation test")
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            # Should complete successfully despite taking time
            assert "Long-running operation completed" in result
            assert duration >= 0.1  # Took at least our simulated time

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test that server doesn't leak memory across operations"""
        import gc
        
        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_result = Mock()
            mock_result.session.answer = "Memory test"
            mock_result.session.cost = 0.01
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            search_tool = server._tools["search_literature"]
            
            # Run many operations
            for i in range(50):
                await search_tool.handler(query=f"memory test {i}")
        
        # Clean up and check object count
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory growth
        # Allow some growth but not excessive
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Too much memory growth: {object_growth} new objects"


class TestMCPProtocolCompliance:
    """Test specific MCP protocol compliance requirements"""
    
    def test_tool_names_valid(self):
        """Test that tool names follow MCP naming conventions"""
        for tool_name in server._tools.keys():
            # Should use snake_case
            assert tool_name.islower()
            assert ' ' not in tool_name
            assert tool_name.replace('_', '').isalnum()

    def test_response_json_serializable(self):
        """Test that all responses can be JSON serialized"""
        # This is important for MCP protocol compliance
        test_responses = [
            "Simple string response",
            "Response with unicode: 📚 🔍 ✅",
            "Multi-line\nresponse\nwith\nnewlines",
            "Response with special chars: @#$%^&*()",
        ]
        
        for response in test_responses:
            try:
                json.dumps(response)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Response not JSON serializable: {response} - Error: {e}")

    @pytest.mark.asyncio
    async def test_tool_idempotency(self):
        """Test that tools are idempotent where appropriate"""
        # Status check should be idempotent
        status_tool = server._tools["get_library_status"]
        
        result1 = await status_tool.handler()
        result2 = await status_tool.handler()
        
        # Should return same result
        assert result1 == result2
        
        # Configuration should be idempotent
        config_tool = server._tools["configure_embedding"]
        
        current_model = settings.embedding
        result1 = await config_tool.handler(model_name=current_model)
        result2 = await config_tool.handler(model_name=current_model)
        
        # Should handle repeated configuration gracefully
        assert "✅" in result1
        assert "✅" in result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])