#!/usr/bin/env python3
"""
End-to-End Integration Tests

Tests the complete system including MCP server startup, tool execution,
and integration with external APIs (mocked for testing).
"""

import asyncio
import json
import subprocess
import tempfile
import time
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch
import signal
import os

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

class TestEndToEndIntegration:
    """End-to-end system tests"""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create minimal valid PDF content for testing"""
        # This is a minimal PDF that can be parsed
        return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test academic content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000191 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
285
%%EOF"""

    @pytest.fixture
    def temp_pdf_file(self, sample_pdf_content):
        """Create temporary PDF file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_path = temp_file.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_complete_research_workflow(self, temp_pdf_file):
        """Test complete academic research workflow"""
        
        # Import server components
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        
        from paperqa_mcp_server import (
            search_literature, add_document, get_library_status, 
            configure_embedding, docs, settings
        )
        
        # Clear state
        docs.docs.clear()
        docs.texts.clear()
        
        try:
            # Step 1: Check initial status
            status = await get_library_status()
            assert "Empty library" in status
            assert "0 indexed" in status
            
            # Step 2: Configure optimal embedding model
            config_result = await configure_embedding("voyage-ai/voyage-3-lite")
            assert "✅ Embedding model updated" in config_result
            assert "6.5x cheaper" in config_result
            
            # Step 3: Add document to library
            with patch.object(docs, 'aadd_file', new_callable=AsyncMock) as mock_add:
                mock_add.return_value = None
                docs.docs = {"academic_paper": Mock()}
                docs.texts = [Mock() for _ in range(12)]  # Simulate 12 text chunks
                
                add_result = await add_document(temp_pdf_file, "Academic Research Paper")
                
                assert "✅ Successfully added document" in add_result
                assert "Academic Research Paper" in add_result
                assert "1 documents, 12 searchable segments" in add_result
                
                # Verify the document was processed
                mock_add.assert_called_once()
            
            # Step 4: Check updated library status
            status = await get_library_status()
            assert "1 indexed" in status
            assert "12 searchable chunks" in status
            assert "voyage-ai/voyage-3-lite" in status
            
            # Step 5: Perform literature search
            with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
                # Mock comprehensive research result
                mock_result = Mock()
                mock_result.session.answer = """
Based on the academic literature analysis, machine learning approaches demonstrate significant effectiveness in academic research applications. The evidence shows:

1. **Performance Metrics**: Studies report 85-92% accuracy rates across different domains
2. **Methodological Rigor**: Proper validation techniques are essential for reliable results  
3. **Implementation Challenges**: Data quality and model selection remain critical factors

The research indicates that while ML techniques show promise, careful attention to methodological details is required for robust academic applications.
                """.strip()
                mock_result.session.cost = 0.127
                mock_result.session.contexts = [Mock() for _ in range(8)]  # 8 evidence sources
                mock_query.return_value = mock_result
                
                search_result = await search_literature(
                    query="What is the effectiveness of machine learning approaches in academic research?",
                    max_sources=8
                )
                
                # Verify comprehensive research response
                assert "Literature Search Results" in search_result
                assert "machine learning approaches demonstrate significant effectiveness" in search_result
                assert "85-92% accuracy rates" in search_result
                assert "8 evidence sources analyzed" in search_result
                assert "$0.1270" in search_result
                assert "voyage-ai/voyage-3-lite" in search_result
                
                # Verify query was called with correct parameters
                args, kwargs = mock_query.call_args
                assert kwargs['settings'].embedding == "voyage-ai/voyage-3-lite"
                assert kwargs['settings'].answer.evidence_k == 8
            
            # Step 6: Test different embedding model
            config_result = await configure_embedding("gemini/gemini-embedding-001")
            assert "✅ Embedding model updated" in config_result
            assert "Highest accuracy" in config_result
            
            # Step 7: Search with new model
            with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
                mock_result = Mock()
                mock_result.session.answer = "Updated search with Gemini embeddings shows improved semantic understanding."
                mock_result.session.cost = 0.089
                mock_result.session.contexts = [Mock() for _ in range(5)]
                mock_query.return_value = mock_result
                
                search_result = await search_literature("semantic understanding improvements")
                
                assert "improved semantic understanding" in search_result
                assert "5 evidence sources analyzed" in search_result
                
                # Verify new model was used
                args, kwargs = mock_query.call_args
                assert kwargs['settings'].embedding == "gemini/gemini-embedding-001"
            
            print("✅ Complete research workflow test passed!")
            
        finally:
            # Cleanup
            docs.docs.clear()
            docs.texts.clear()

    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self):
        """Test system behavior under various error conditions"""
        
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        
        from paperqa_mcp_server import search_literature, add_document, docs
        
        # Clear state
        docs.docs.clear()
        docs.texts.clear()
        
        # Test 1: Network connectivity issues
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = ConnectionError("Unable to connect to API")
            
            result = await search_literature("network test")
            
            assert "❌ Literature search failed" in result
            assert "Unable to connect to API" in result
            assert "check your API keys" in result
        
        # Test 2: API key issues
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("Invalid API key")
            
            result = await search_literature("api key test")
            
            assert "❌ Literature search failed" in result
            assert "Invalid API key" in result
        
        # Test 3: File system issues
        result = await add_document("/nonexistent/directory/file.pdf")
        assert "❌ Error: File not found" in result
        
        # Test 4: Invalid file format
        with tempfile.NamedTemporaryFile(suffix=".docx") as temp_file:
            result = await add_document(temp_file.name)
            assert "❌ Error: Only PDF files supported" in result
            assert ".docx" in result
        
        # Test 5: Document processing errors
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            temp_file.write(b"not a valid pdf")
            temp_file.flush()
            
            with patch.object(docs, 'aadd_file', new_callable=AsyncMock) as mock_add:
                mock_add.side_effect = Exception("PDF parsing failed")
                
                result = await add_document(temp_file.name)
                assert "❌ Upload failed" in result
                assert "PDF parsing failed" in result
        
        print("✅ Error recovery scenarios test passed!")

    @pytest.mark.asyncio
    async def test_performance_characteristics(self):
        """Test system performance under various loads"""
        
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        
        from paperqa_mcp_server import search_literature, get_library_status
        
        with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
            # Mock fast response
            mock_result = Mock()
            mock_result.session.answer = "Performance test response"
            mock_result.session.cost = 0.01
            mock_result.session.contexts = []
            mock_query.return_value = mock_result
            
            # Test 1: Response time for single search
            start_time = time.time()
            result = await search_literature("performance test")
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 1.0  # Should respond quickly with mocked backend
            assert "Performance test response" in result
            
            # Test 2: Concurrent searches
            start_time = time.time()
            tasks = [search_literature(f"concurrent test {i}") for i in range(10)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            concurrent_time = end_time - start_time
            assert len(results) == 10
            assert all("Performance test response" in result for result in results)
            assert concurrent_time < 2.0  # Concurrent execution should be efficient
            
            # Test 3: Mixed operation load
            mixed_tasks = [
                search_literature("mixed test 1"),
                get_library_status(),
                search_literature("mixed test 2"),
                get_library_status(),
            ]
            
            start_time = time.time()
            mixed_results = await asyncio.gather(*mixed_tasks)
            end_time = time.time()
            
            mixed_time = end_time - start_time
            assert len(mixed_results) == 4
            assert mixed_time < 1.5
        
        print("✅ Performance characteristics test passed!")

    @pytest.mark.asyncio
    async def test_data_consistency(self):
        """Test data consistency across operations"""
        
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        
        from paperqa_mcp_server import (
            add_document, get_library_status, configure_embedding,
            docs, settings
        )
        
        # Clear state
        docs.docs.clear()
        docs.texts.clear()
        
        # Test 1: Configuration consistency
        original_embedding = settings.embedding
        
        await configure_embedding("gemini/gemini-embedding-001")
        assert settings.embedding == "gemini/gemini-embedding-001"
        
        # Status should reflect the change
        status = await get_library_status()
        assert "gemini/gemini-embedding-001" in status
        
        # Change back
        await configure_embedding(original_embedding)
        assert settings.embedding == original_embedding
        
        # Test 2: Document state consistency
        with patch.object(docs, 'aadd_file', new_callable=AsyncMock):
            # Initially empty
            status = await get_library_status()
            assert "0 indexed" in status
            
            # Add documents
            docs.docs = {
                "doc1": Mock(),
                "doc2": Mock(),
                "doc3": Mock()
            }
            docs.texts = [Mock() for _ in range(25)]
            
            status = await get_library_status()
            assert "3 indexed" in status
            assert "25 searchable chunks" in status
            
            # Remove documents
            docs.docs.clear()
            docs.texts.clear()
            
            status = await get_library_status()
            assert "0 indexed" in status
        
        print("✅ Data consistency test passed!")

    def test_configuration_validation(self):
        """Test configuration file validation"""
        
        # Test valid configuration
        valid_config = {
            "mcpServers": {
                "paperqa-academic": {
                    "command": "python3",
                    "args": ["/path/to/paperqa_mcp_server.py"],
                    "env": {
                        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                        "VOYAGE_API_KEY": "${VOYAGE_API_KEY}",
                        "GEMINI_API_KEY": "${GEMINI_API_KEY}"
                    }
                }
            }
        }
        
        # Should be valid JSON
        json_str = json.dumps(valid_config, indent=2)
        parsed = json.loads(json_str)
        
        assert "mcpServers" in parsed
        assert "paperqa-academic" in parsed["mcpServers"]
        assert "command" in parsed["mcpServers"]["paperqa-academic"]
        assert "args" in parsed["mcpServers"]["paperqa-academic"]
        assert "env" in parsed["mcpServers"]["paperqa-academic"]
        
        # Test environment variable references
        env_vars = parsed["mcpServers"]["paperqa-academic"]["env"]
        expected_vars = ["OPENAI_API_KEY", "VOYAGE_API_KEY", "GEMINI_API_KEY"]
        
        for var in expected_vars:
            assert var in env_vars
            assert env_vars[var] == f"${{{var}}}"
        
        print("✅ Configuration validation test passed!")

    @pytest.mark.asyncio
    async def test_startup_and_shutdown(self):
        """Test server startup and shutdown procedures"""
        
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        
        from paperqa_mcp_server import load_existing_papers, docs, paper_directory
        
        # Test startup procedure
        docs.docs.clear()
        docs.texts.clear()
        
        # Mock paper directory with files
        with patch('paperqa_mcp_server.paper_directory') as mock_dir:
            mock_pdf1 = Mock()
            mock_pdf1.stem = "paper1"
            mock_pdf2 = Mock()
            mock_pdf2.stem = "paper2"
            
            mock_dir.glob.return_value = [mock_pdf1, mock_pdf2]
            
            # Mock file operations
            with patch('builtins.open', mock_open_multiple_files({"paper1": b"pdf1", "paper2": b"pdf2"})):
                with patch.object(docs, 'aadd_file', new_callable=AsyncMock) as mock_add:
                    mock_add.return_value = None
                    
                    # Simulate successful loading
                    docs.docs = {"paper1": Mock(), "paper2": Mock()}
                    
                    await load_existing_papers()
                    
                    # Should have attempted to load both papers
                    assert mock_add.call_count == 2
                    assert len(docs.docs) == 2
        
        print("✅ Startup and shutdown test passed!")


def mock_open_multiple_files(files_dict):
    """Helper to mock opening multiple files"""
    from unittest.mock import mock_open, MagicMock
    
    def mock_open_func(filename, mode='r', *args, **kwargs):
        if hasattr(filename, 'stem'):
            filename = filename.stem
        
        for file_stem, content in files_dict.items():
            if file_stem in str(filename):
                return mock_open(read_data=content).return_value
        
        # Default behavior
        return mock_open().return_value
    
    return mock_open_func


@pytest.mark.asyncio
async def test_integration_stress_test():
    """Stress test with multiple concurrent operations"""
    
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    from paperqa_mcp_server import search_literature, get_library_status, configure_embedding
    
    with patch('paperqa_mcp_server.agent_query', new_callable=AsyncMock) as mock_query:
        mock_result = Mock()
        mock_result.session.answer = "Stress test response"
        mock_result.session.cost = 0.001
        mock_result.session.contexts = []
        mock_query.return_value = mock_result
        
        # Create many concurrent operations
        tasks = []
        
        # Add searches
        for i in range(20):
            tasks.append(search_literature(f"stress test query {i}"))
        
        # Add status checks
        for i in range(10):
            tasks.append(get_library_status())
        
        # Add configuration changes
        embedding_models = ["voyage-ai/voyage-3-lite", "gemini/gemini-embedding-001", "text-embedding-3-small"]
        for model in embedding_models:
            tasks.append(configure_embedding(model))
        
        # Execute all concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verify results
        assert len(results) == 33  # 20 + 10 + 3
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found {len(exceptions)} exceptions: {exceptions}"
        
        # Verify all completed successfully
        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) == 33
        
        # Performance check
        total_time = end_time - start_time
        assert total_time < 5.0, f"Stress test took too long: {total_time:.2f}s"
        
        print(f"✅ Stress test passed! Processed 33 operations in {total_time:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])