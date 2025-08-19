#!/usr/bin/env python3
"""
Test Runner for PaperQA2 MCP Server Integration Tests

Runs all integration tests and provides comprehensive reporting.
"""

import asyncio
import sys
import subprocess
import time
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_pytest_suite():
    """Run the complete pytest suite with proper configuration"""
    
    print("🧪 Running PaperQA2 MCP Server Integration Test Suite")
    print("=" * 60)
    
    test_dir = Path(__file__).parent
    
    # Test modules to run
    test_modules = [
        "embedding/test_embedding_simple.py",
        "integration/test_mcp_server.py",
        "integration/test_paperqa_mcp_integration.py", 
        "integration/test_mcp_protocol.py",
        "integration/test_end_to_end.py"
    ]
    
    all_results = []
    total_start_time = time.time()
    
    for module in test_modules:
        test_path = test_dir / module
        if not test_path.exists():
            print(f"⚠️  Test module not found: {test_path}")
            continue
        
        print(f"\n📋 Running: {module}")
        print("-" * 40)
        
        start_time = time.time()
        
        # Run pytest for this module
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_path),
            "-v",
            "--tb=short",
            "--capture=no", 
            "--disable-warnings",
            "--asyncio-mode=auto"  # Enable asyncio support
        ], capture_output=True, text=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse results
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        
        print(f"{status} - {module} ({duration:.2f}s)")
        
        if not success:
            print(f"❌ Error output:")
            print(result.stderr)
            print(f"📄 Standard output:")
            print(result.stdout)
        else:
            # Count tests from output
            output_lines = result.stdout.split('\n')
            test_summary_line = [line for line in output_lines if "passed" in line and "failed" in line]
            if test_summary_line:
                print(f"   {test_summary_line[-1].strip()}")
        
        all_results.append({
            "module": module,
            "success": success,
            "duration": duration,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)
    
    passed_count = sum(1 for r in all_results if r["success"])
    failed_count = len(all_results) - passed_count
    
    print(f"📈 Total Modules: {len(all_results)}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️  Total Time: {total_duration:.2f}s")
    print(f"🎯 Success Rate: {(passed_count/len(all_results)*100):.1f}%")
    
    if failed_count > 0:
        print(f"\n❌ FAILED MODULES:")
        for result in all_results:
            if not result["success"]:
                print(f"   - {result['module']}")
    
    # Save detailed results
    results_file = test_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "total_modules": len(all_results),
                "passed": passed_count,
                "failed": failed_count,
                "success_rate": passed_count/len(all_results)*100,
                "total_duration": total_duration,
                "timestamp": time.time()
            },
            "results": all_results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return failed_count == 0

def check_test_requirements():
    """Check that test requirements are available"""
    
    print("🔍 Checking test requirements...")
    
    required_packages = [
        ("pytest", "pytest"),
        ("paperqa", "paper-qa"), 
        ("mcp", "mcp"),
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {import_name} available")
        except ImportError:
            print(f"   ❌ {import_name} missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All requirements available")
    return True

def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality"""
    
    print("\n🔥 Running smoke test...")
    
    try:
        # Test basic imports
        from paperqa_mcp_server import server, settings, docs
        print("   ✅ MCP server imports successful")
        
        # Test tool registration - verify tools can be listed
        # Note: list_tools is async in FastMCP, so we'll check the server has the method
        assert hasattr(server, 'list_tools'), "Server missing list_tools method"
        assert callable(getattr(server, 'list_tools')), "list_tools not callable"
        print(f"   ✅ Tool registration interface available")
        
        # Test settings
        assert settings.embedding in ["voyage-ai/voyage-3-lite", "gemini/gemini-embedding-001", "text-embedding-3-small"]
        print(f"   ✅ Settings valid (embedding: {settings.embedding})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Smoke test failed: {e}")
        return False

async def run_async_smoke_test():
    """Run async smoke test of core functionality"""
    
    print("🔄 Running async smoke test...")
    
    try:
        from paperqa_mcp_server import get_library_status, configure_embedding, server, settings
        
        # Test tool listing
        tools = await server.list_tools()
        tool_names = [tool.name for tool in tools]
        expected_tools = ["search_literature", "add_document", "get_library_status", "configure_embedding"]
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found in {tool_names}"
        print(f"   ✅ All 4 tools registered: {tool_names}")
        
        # Test status check
        status = await get_library_status()
        assert isinstance(status, str)
        assert "Research Library Status" in status
        print("   ✅ Library status check works")
        
        # Test configuration
        current_model = settings.embedding
        config_result = await configure_embedding(current_model)
        assert isinstance(config_result, str)
        assert "✅ Embedding model updated" in config_result
        print("   ✅ Model configuration works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Async smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    
    print("🚀 PaperQA2 MCP Server - Integration Test Suite")
    print("=" * 60)
    
    # Check requirements first
    if not check_test_requirements():
        sys.exit(1)
    
    # Run smoke tests
    if not run_quick_smoke_test():
        print("❌ Smoke test failed - aborting full test suite")
        sys.exit(1)
    
    # Run async smoke test
    if not asyncio.run(run_async_smoke_test()):
        print("❌ Async smoke test failed - aborting full test suite")
        sys.exit(1)
    
    print("✅ Smoke tests passed - proceeding with full test suite")
    
    # Run full test suite
    success = run_pytest_suite()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ PaperQA2 MCP Server is ready for production use")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        print("🔧 Review the failures above and fix issues before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()