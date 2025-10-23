#!/usr/bin/env python3
"""
Simple test runner for YouTubeTranscriptFetcher
Usage: python test_runner.py [test_name]
"""

import sys
import os
from test_transcript_fetcher import TestYouTubeTranscriptFetcher

def main():
    """Main test runner with optional specific test selection"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        tester = TestYouTubeTranscriptFetcher()
        tester.setup_test_environment()
        
        try:
            if test_name == "init":
                tester.run_test("Initialization", tester.test_initialization)
            elif test_name == "direct":
                tester.run_test("Direct Connection Mode", tester.test_direct_connection_mode)
            elif test_name == "proxy":
                tester.run_test("Proxy Mode", tester.test_proxy_mode)
            elif test_name == "cache":
                tester.run_test("Caching Functionality", tester.test_caching_functionality)
            elif test_name == "force":
                tester.run_test("Force Refresh", tester.test_force_refresh)
            elif test_name == "concurrent":
                tester.run_test("Concurrent Requests", tester.test_concurrent_requests)
            elif test_name == "error":
                tester.run_test("Error Handling", tester.test_error_handling)
            elif test_name == "flattened":
                tester.run_test("Generate Flattened", tester.test_generate_flattened)
            elif test_name == "useragent":
                tester.run_test("User Agent Rotation", tester.test_user_agent_rotation)
            elif test_name == "cache_structure":
                tester.run_test("Cache Directory Structure", tester.test_cache_directory_structure)
            else:
                print(f"Unknown test: {test_name}")
                print("Available tests: init, direct, proxy, cache, force, concurrent, error, flattened, useragent, cache_structure")
                sys.exit(1)
            
            tester.print_test_summary()
            
        finally:
            tester.cleanup_test_environment()
    else:
        # Run all tests
        tester = TestYouTubeTranscriptFetcher()
        tester.run_all_tests()

if __name__ == "__main__":
    main()
