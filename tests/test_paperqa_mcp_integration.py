#!/usr/bin/env python3
"""
Integration Test Suite for PaperQA2 MCP Server

Tests the complete integration between the MCP server and PaperQA2,
including tool functionality, error handling, and real document processing.
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import our MCP server components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from paperqa_mcp_server import (
    search_literature, add_document, get_library_status, 
    configure_embedding, load_existing_papers, docs, settings
)
from paperqa import Settings, Docs

class TestPaperQAMCPIntegration:
    """Integration tests for the PaperQA2 MCP server"""
    
    @pytest.fixture(autouse=True)
    async def setup_and_cleanup(self):
        """Clean setup and teardown for each test"""
        # Clear docs state before each test
        docs.docs.clear()
        docs.texts.clear()
        
        # Reset settings to default
        settings.embedding = "voyage-ai/voyage-3-lite"
        settings.llm = "gpt-4o-2024-11-20"
        settings.answer.evidence_k = 8
        
        yield
        
        # Cleanup after test
        docs.docs.clear()
        docs.texts.clear()

    @pytest.mark.asyncio
    async def test_get_library_status_empty(self):
        """Test library status when empty"""
        result = await get_library_status()
        
        assert "Empty library" in result
        assert "0 indexed" in result
        assert "voyage-ai/voyage-3-lite" in result
        assert "gpt-4o-2024-11-20" in result

    @pytest.mark.asyncio
    async def test_configure_embedding_valid_models(self):
        """Test embedding model configuration with valid models"""
        # Test Voyage AI (default)
        result = await configure_embedding("voyage-ai/voyage-3-lite")
        assert "✅ Embedding model updated" in result
        assert settings.embedding == "voyage-ai/voyage-3-lite"
        
        # Test Gemini
        result = await configure_embedding("gemini/gemini-embedding-001")
        assert "✅ Embedding model updated" in result
        assert settings.embedding == "gemini/gemini-embedding-001"
        
        # Test OpenAI
        result = await configure_embedding("text-embedding-3-small")
        assert "✅ Embedding model updated" in result
        assert settings.embedding == "text-embedding-3-small"

    @pytest.mark.asyncio
    async def test_configure_embedding_invalid_model(self):
        """Test embedding configuration with invalid model"""
        result = await configure_embedding("invalid-model")
        
        assert "❌ Unsupported embedding model" in result
        assert "voyage-ai/voyage-3-lite" in result
        assert "gemini/gemini-embedding-001" in result
        assert "text-embedding-3-small" in result

    @pytest.mark.asyncio
    async def test_add_document_file_not_found(self):
        """Test document upload with non-existent file"""
        result = await add_document("/nonexistent/path.pdf")
        
        assert "❌ Error: File not found" in result

    @pytest.mark.asyncio
    async def test_add_document_invalid_format(self):
        """Test document upload with invalid file format"""
        with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
            result = await add_document(temp_file.name)
            
            assert "❌ Error: Only PDF files supported" in result
            assert ".txt" in result

    @pytest.mark.asyncio
    async def test_add_document_success_mock(self):
        """Test successful document upload with mocked PaperQA2"""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4 test content")
            temp_path = temp_file.name
        
        try:
            # Mock the docs.aadd_file method
            with patch.object(docs, 'aadd_file', new_callable=AsyncMock) as mock_add:
                mock_add.return_value = None
                
                # Mock docs collections for status
                docs.docs = {"test_doc": Mock()}
                docs.texts = [Mock() for _ in range(5)]
                
                result = await add_document(temp_path, "Test Document")
                
                assert "✅ Successfully added document" in result
                assert "Test Document" in result
                assert "1 documents, 5 searchable segments" in result
                
                # Verify aadd_file was called
                mock_add.assert_called_once()
                
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio 
    async def test_search_literature_no_docs(self):
        """Test literature search with empty library"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Mock empty result
            mock_result = Mock()
            mock_result.session.answer = "No relevant documents found."
            mock_result.session.cost = 0.01
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            result = await search_literature("test query")
            
            assert "Literature Search Results" in result
            assert "No relevant documents found" in result
            assert "0 evidence sources analyzed" in result
            assert "$0.0100" in result

    @pytest.mark.asyncio
    async def test_search_literature_with_results(self):
        """Test literature search with mocked results"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Mock successful result
            mock_result = Mock()
            mock_result.session.answer = "Based on the literature, machine learning approaches show promising results."
            mock_result.session.cost = 0.05
            mock_result.session.contexts = [Mock(), Mock(), Mock()]  # 3 sources
            mock_query.return_value = mock_result
            
            result = await search_literature("machine learning effectiveness", max_sources=3)
            
            assert "Literature Search Results" in result
            assert "machine learning approaches show promising results" in result
            assert "3 evidence sources analyzed" in result
            assert "$0.0500" in result
            assert "voyage-ai/voyage-3-lite" in result

    @pytest.mark.asyncio
    async def test_search_literature_error_handling(self):
        """Test search error handling"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("API key not found")
            
            result = await search_literature("test query")
            
            assert "❌ Literature search failed" in result
            assert "API key not found" in result
            assert "check your API keys" in result

    @pytest.mark.asyncio
    async def test_max_sources_parameter(self):
        """Test max_sources parameter validation"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_result = Mock()
            mock_result.session.answer = "Test answer"
            mock_result.session.cost = 0.02
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            # Test valid range
            await search_literature("test", max_sources=10)
            # Should set evidence_k to 10
            args, kwargs = mock_query.call_args
            assert kwargs['settings'].answer.evidence_k == 10
            
            # Test boundary conditions
            await search_literature("test", max_sources=1)  # Should work
            await search_literature("test", max_sources=15)  # Should work
            
            # Test invalid values (should be ignored, use default)
            await search_literature("test", max_sources=0)  # Should ignore
            await search_literature("test", max_sources=20)  # Should ignore

    @pytest.mark.asyncio
    async def test_library_status_with_documents(self):
        """Test library status with documents present"""
        # Mock documents in library
        mock_doc = Mock()
        mock_doc.docname = "Test Paper"
        docs.docs = {"test_paper": mock_doc}
        docs.texts = [Mock() for _ in range(25)]  # 25 text segments
        
        with patch('paperqa_mcp_server.paper_directory') as mock_dir:
            mock_dir.glob.return_value = [Mock(stat=Mock(return_value=Mock(st_size=1024*1024)))]
            
            result = await get_library_status()
            
            assert "1 indexed" in result
            assert "25 searchable chunks" in result
            assert "Test Paper" in result
            assert "1.0 MB" in result

    @pytest.mark.asyncio
    async def test_error_handling_robustness(self):
        """Test that all tools handle errors gracefully"""
        # Test search with network error
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = ConnectionError("Network error")
            result = await search_literature("test")
            assert "❌ Literature search failed" in result
            assert "Network error" in result
        
        # Test status with file system error
        with patch('paperqa_mcp_server.paper_directory') as mock_dir:
            mock_dir.glob.side_effect = PermissionError("Access denied")
            result = await get_library_status()
            assert "❌ Status check failed" in result

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent tool operations"""
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_result = Mock()
            mock_result.session.answer = "Concurrent test"
            mock_result.session.cost = 0.01
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            # Run multiple searches concurrently
            tasks = [
                search_literature("query 1"),
                search_literature("query 2"),
                get_library_status()
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all("search failed" not in result for result in results[:2])
            assert "Research Library Status" in results[2]

    @pytest.mark.asyncio
    async def test_settings_persistence(self):
        """Test that settings changes persist across operations"""
        # Change embedding model
        await configure_embedding("gemini/gemini-embedding-001")
        
        # Verify it's used in search
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_result = Mock()
            mock_result.session.answer = "Test"
            mock_result.session.cost = 0.01
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            await search_literature("test")
            
            # Check that Gemini model was used
            args, kwargs = mock_query.call_args
            assert kwargs['settings'].embedding == "gemini/gemini-embedding-001"
        
        # Verify status shows correct model
        result = await get_library_status()
        assert "gemini/gemini-embedding-001" in result


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete workflow: configure -> add document -> search"""
    # This would be an end-to-end test with real PaperQA2
    # For now, we'll mock the components but test the full flow
    
    with patch.object(docs, 'aadd_file', new_callable=AsyncMock) as mock_add:
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Setup mocks
            mock_add.return_value = None
            mock_result = Mock()
            mock_result.session.answer = "Research shows positive results."
            mock_result.session.cost = 0.03
            mock_result.session.contexts = [Mock(), Mock()]
            mock_query.return_value = mock_result
            
            # Mock document state
            docs.docs = {"test": Mock()}
            docs.texts = [Mock() for _ in range(10)]
            
            # 1. Configure embedding
            config_result = await configure_embedding("gemini/gemini-embedding-001")
            assert "✅ Embedding model updated" in config_result
            
            # 2. Add document (using temporary file)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(b"%PDF-1.4 test")
                temp_path = temp_file.name
            
            try:
                add_result = await add_document(temp_path, "Research Paper")
                assert "✅ Successfully added document" in add_result
                
                # 3. Check status
                status_result = await get_library_status()
                assert "gemini/gemini-embedding-001" in status_result
                assert "1 indexed" in status_result
                
                # 4. Search literature
                search_result = await search_literature("research effectiveness")
                assert "Research shows positive results" in search_result
                assert "2 evidence sources" in search_result
                
            finally:
                Path(temp_path).unlink()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])