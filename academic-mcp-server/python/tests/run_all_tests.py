#!/usr/bin/env python3
"""
Comprehensive test runner for the Academic MCP Server testing framework

This script runs all test suites and generates a comprehensive test report.
"""

import sys
import os
import time
import json
from pathlib import Path
import subprocess
import argparse
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    """Comprehensive test runner for all test suites"""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.results_dir = self.tests_dir / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_suites = {
            'basic_functionality': {
                'file': 'test_basic_functionality.py',
                'description': 'Basic functionality and import tests',
                'category': 'unit',
                'required': True
            },
            'text_extraction': {
                'file': 'test_text_extraction.py',
                'description': 'Text extraction component tests',
                'category': 'unit',
                'required': True
            },
            'structure_detection': {
                'file': 'test_structure_detection.py',
                'description': 'Document structure detection tests',
                'category': 'unit',
                'required': True
            },
            'metadata_extraction': {
                'file': 'test_metadata_extraction.py',
                'description': 'Metadata extraction and validation tests',
                'category': 'unit',
                'required': True
            },
            'multicolumn_layout': {
                'file': 'test_multicolumn_layout.py',
                'description': 'Multi-column layout handling tests',
                'category': 'unit',
                'required': True
            },
            'nlp_pipeline': {
                'file': 'text_chunking/test_nlp_pipeline.py',
                'description': 'NLP pipeline and text chunking tests',
                'category': 'unit',
                'required': True
            },
            'end_to_end_integration': {
                'file': 'integration/test_end_to_end_processing.py',
                'description': 'End-to-end PDF processing pipeline tests',
                'category': 'integration',
                'required': True
            },
            'regression_tests': {
                'file': 'test_regression.py',
                'description': 'Regression tests for quality maintenance',
                'category': 'regression',
                'required': False
            },
            'performance_benchmarks': {
                'file': 'performance/test_benchmarks.py',
                'description': 'Performance and memory benchmarks',
                'category': 'performance',
                'required': False
            }
        }
    
    def run_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test suite"""
        print(f"\\n🔍 Running {suite_name}: {suite_config['description']}")
        
        test_file = self.tests_dir / suite_config['file']
        if not test_file.exists():
            return {
                'suite': suite_name,
                'status': 'skipped',
                'reason': 'Test file not found',
                'execution_time': 0,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
        
        start_time = time.time()
        
        try:
            # Run pytest on the test file
            cmd = [sys.executable, '-m', 'pytest', str(test_file), '-v', '--tb=short']
            
            # Add performance markers for benchmark tests
            if suite_config['category'] == 'performance':
                cmd.extend(['-m', 'performance'])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.tests_dir,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse pytest output
            output_lines = result.stdout.split('\\n')
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            
            for line in output_lines:
                if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                    tests_run += 1
                    if 'PASSED' in line:
                        tests_passed += 1
                    elif 'FAILED' in line:
                        tests_failed += 1
            
            # Determine status
            if result.returncode == 0:
                status = 'passed'
            elif tests_run == 0:
                status = 'skipped'
            else:
                status = 'failed'
            
            return {
                'suite': suite_name,
                'status': status,
                'execution_time': execution_time,
                'tests_run': tests_run,
                'tests_passed': tests_passed,
                'tests_failed': tests_failed,
                'tests_skipped': tests_run - tests_passed - tests_failed,
                'output': result.stdout,
                'errors': result.stderr if result.stderr else None
            }
        
        except subprocess.TimeoutExpired:
            return {
                'suite': suite_name,
                'status': 'timeout',
                'reason': 'Test suite exceeded 5 minute timeout',
                'execution_time': time.time() - start_time,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
        
        except Exception as e:
            return {
                'suite': suite_name,
                'status': 'error',
                'reason': str(e),
                'execution_time': time.time() - start_time,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def run_all_tests(self, categories: Optional[List[str]] = None, required_only: bool = False) -> Dict[str, Any]:
        """Run all test suites with filtering options"""
        print("🧪 Academic MCP Server - Comprehensive Testing Framework")
        print("=" * 60)
        
        start_time = time.time()
        results = []
        
        for suite_name, suite_config in self.test_suites.items():
            # Apply filters
            if categories and suite_config['category'] not in categories:
                continue
            
            if required_only and not suite_config['required']:
                continue
            
            result = self.run_test_suite(suite_name, suite_config)
            results.append(result)
            
            # Print immediate result
            status_emoji = {
                'passed': '✅',
                'failed': '❌', 
                'skipped': '⏭️',
                'timeout': '⏰',
                'error': '💥'
            }.get(result['status'], '❓')
            
            print(f"{status_emoji} {suite_name}: {result['status'].upper()}")
            if result['status'] in ['failed', 'error', 'timeout']:
                if result.get('reason'):
                    print(f"   Reason: {result['reason']}")
                if result.get('tests_failed', 0) > 0:
                    print(f"   Failed: {result['tests_failed']}/{result['tests_run']} tests")
        
        total_time = time.time() - start_time
        
        # Generate summary
        summary = self.generate_summary(results, total_time)
        
        # Save detailed results
        self.save_results(results, summary)
        
        # Print summary
        self.print_summary(summary)
        
        return {
            'summary': summary,
            'detailed_results': results,
            'total_execution_time': total_time
        }
    
    def generate_summary(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Generate test run summary"""
        total_suites = len(results)
        passed_suites = len([r for r in results if r['status'] == 'passed'])
        failed_suites = len([r for r in results if r['status'] == 'failed'])
        skipped_suites = len([r for r in results if r['status'] == 'skipped'])
        error_suites = len([r for r in results if r['status'] in ['error', 'timeout']])
        
        total_tests = sum(r.get('tests_run', 0) for r in results)
        total_passed = sum(r.get('tests_passed', 0) for r in results)
        total_failed = sum(r.get('tests_failed', 0) for r in results)
        total_skipped = sum(r.get('tests_skipped', 0) for r in results)
        
        # Calculate success rates
        suite_success_rate = (passed_suites / total_suites * 100) if total_suites > 0 else 0
        test_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize results
        categories = {}
        for result in results:
            suite_config = self.test_suites.get(result['suite'], {})
            category = suite_config.get('category', 'unknown')
            
            if category not in categories:
                categories[category] = {
                    'suites': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'tests_total': 0,
                    'tests_passed': 0
                }
            
            categories[category]['suites'] += 1
            categories[category]['tests_total'] += result.get('tests_run', 0)
            categories[category]['tests_passed'] += result.get('tests_passed', 0)
            
            if result['status'] == 'passed':
                categories[category]['passed'] += 1
            elif result['status'] == 'failed':
                categories[category]['failed'] += 1
            else:
                categories[category]['skipped'] += 1
        
        return {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_execution_time': total_time,
            'suite_summary': {
                'total': total_suites,
                'passed': passed_suites,
                'failed': failed_suites,
                'skipped': skipped_suites,
                'errors': error_suites,
                'success_rate': suite_success_rate
            },
            'test_summary': {
                'total': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'success_rate': test_success_rate
            },
            'categories': categories,
            'overall_status': 'PASSED' if failed_suites == 0 and error_suites == 0 else 'FAILED'
        }
    
    def save_results(self, results: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Save test results to files"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Save detailed results
        detailed_file = self.results_dir / f"test_results_{timestamp}.json"
        with open(detailed_file, 'w') as f:
            json.dump({
                'summary': summary,
                'results': results
            }, f, indent=2, default=str)
        
        # Save summary report
        summary_file = self.results_dir / f"test_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Update latest results symlinks
        latest_detailed = self.results_dir / "latest_detailed_results.json"
        latest_summary = self.results_dir / "latest_summary.json"
        
        try:
            if latest_detailed.exists():
                latest_detailed.unlink()
            latest_detailed.symlink_to(detailed_file.name)
            
            if latest_summary.exists():
                latest_summary.unlink()
            latest_summary.symlink_to(summary_file.name)
        except OSError:
            # Fallback for systems without symlink support
            import shutil
            shutil.copy2(detailed_file, latest_detailed)
            shutil.copy2(summary_file, latest_summary)
        
        print(f"\\n📁 Results saved to {self.results_dir}")
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test run summary"""
        print("\\n" + "=" * 60)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 60)
        
        suite_summary = summary['suite_summary']
        test_summary = summary['test_summary']
        
        print(f"🏷️  Test Suites: {suite_summary['passed']}/{suite_summary['total']} passed ({suite_summary['success_rate']:.1f}%)")
        print(f"🧪 Individual Tests: {test_summary['passed']}/{test_summary['total']} passed ({test_summary['success_rate']:.1f}%)")
        print(f"⏱️  Execution Time: {summary['total_execution_time']:.1f} seconds")
        print(f"📅 Timestamp: {summary['timestamp']}")
        
        print(f"\\n🎯 Overall Status: {summary['overall_status']}")
        
        if suite_summary['failed'] > 0 or suite_summary['errors'] > 0:
            print(f"❌ Failed Suites: {suite_summary['failed']}")
            print(f"💥 Error Suites: {suite_summary['errors']}")
        
        if suite_summary['skipped'] > 0:
            print(f"⏭️  Skipped Suites: {suite_summary['skipped']}")
        
        # Print category breakdown
        if summary['categories']:
            print(f"\\n📂 Results by Category:")
            for category, stats in summary['categories'].items():
                success_rate = (stats['passed'] / stats['suites'] * 100) if stats['suites'] > 0 else 0
                print(f"   {category.title()}: {stats['passed']}/{stats['suites']} suites ({success_rate:.1f}%)")
        
        print("=" * 60)


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Run Academic MCP Server test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                    # Run all tests
  python run_all_tests.py --required         # Run only required tests
  python run_all_tests.py --categories unit  # Run only unit tests
  python run_all_tests.py --categories unit integration  # Run unit and integration tests
        """
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['unit', 'integration', 'regression', 'performance'],
        help='Run tests from specific categories only'
    )
    
    parser.add_argument(
        '--required',
        action='store_true',
        help='Run only required test suites'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (excludes performance and regression)'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    categories = args.categories
    if args.quick:
        categories = ['unit', 'integration']
    
    results = runner.run_all_tests(
        categories=categories,
        required_only=args.required
    )
    
    # Exit with appropriate code
    if results['summary']['overall_status'] == 'FAILED':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()