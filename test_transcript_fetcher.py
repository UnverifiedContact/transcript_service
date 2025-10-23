#!/usr/bin/env python3
"""
Comprehensive test script for YouTubeTranscriptFetcher
Tests all functionality including direct connection, proxy mode, caching, and error handling
"""

import os
import sys
import json
import tempfile
import shutil
import time
from unittest.mock import patch, MagicMock
from transcript_fetcher import YouTubeTranscriptFetcher
from utils import Timer, debug_print

# Test configuration
TEST_VIDEO_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (short video)
    "https://youtu.be/dQw4w9WgXcQ",  # Short URL format
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",  # Shorts format
    "dQw4w9WgXcQ",  # Direct video ID
]

# Mock transcript data for testing - using objects with attributes like the real API
class MockTranscriptSegment:
    def __init__(self, text, start, duration):
        self.text = text
        self.start = start
        self.duration = duration

MOCK_TRANSCRIPT_DATA = [
    MockTranscriptSegment("Never gonna give you up", 0.0, 2.5),
    MockTranscriptSegment("Never gonna let you down", 2.5, 2.5),
    MockTranscriptSegment("Never gonna run around and desert you", 5.0, 3.0),
    MockTranscriptSegment("Never gonna make you cry", 8.0, 2.5),
    MockTranscriptSegment("Never gonna say goodbye", 10.5, 2.5),
    MockTranscriptSegment("Never gonna tell a lie and hurt you", 13.0, 3.0),
]

class TestYouTubeTranscriptFetcher:
    """Test class for YouTubeTranscriptFetcher"""
    
    def __init__(self):
        self.test_cache_dir = None
        self.test_results = []
        
    def setup_test_environment(self):
        """Set up temporary test environment"""
        self.test_cache_dir = tempfile.mkdtemp(prefix="test_transcript_cache_")
        debug_print(f"Test cache directory: {self.test_cache_dir}")
        
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.test_cache_dir and os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)
            debug_print(f"Cleaned up test cache directory: {self.test_cache_dir}")
    
    def run_test(self, test_name, test_func):
        """Run a single test and record results"""
        debug_print(f"\n{'='*60}")
        debug_print(f"Running test: {test_name}")
        debug_print(f"{'='*60}")
        
        try:
            with Timer(test_name) as timer:
                result = test_func()
            
            self.test_results.append({
                'name': test_name,
                'status': 'PASSED',
                'duration': timer.get_duration(),
                'result': result
            })
            debug_print(f"✅ {test_name} PASSED ({timer.get_duration()})")
            return result
            
        except Exception as e:
            self.test_results.append({
                'name': test_name,
                'status': 'FAILED',
                'duration': 'N/A',
                'error': str(e)
            })
            debug_print(f"❌ {test_name} FAILED: {e}")
            return None
    
    def test_initialization(self):
        """Test fetcher initialization with different configurations"""
        debug_print("Testing initialization...")
        
        # Test 1: Default initialization
        fetcher1 = YouTubeTranscriptFetcher()
        assert fetcher1.cache_dir == "cache"
        assert fetcher1.force == False
        assert fetcher1.webshare_username is None
        assert fetcher1.webshare_password is None
        assert fetcher1.max_concurrent_requests == 2
        
        # Test 2: Custom initialization
        fetcher2 = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True,
            webshare_username="test_user",
            webshare_password="test_pass",
            max_concurrent_requests=3
        )
        assert fetcher2.cache_dir == self.test_cache_dir
        assert fetcher2.force == True
        assert fetcher2.webshare_username == "test_user"
        assert fetcher2.webshare_password == "test_pass"
        assert fetcher2.max_concurrent_requests == 3
        
        # Test 3: Cache directory creation
        assert os.path.exists(self.test_cache_dir)
        
        return "Initialization tests passed"
    
    def test_direct_connection_mode(self):
        """Test fetcher in direct connection mode (no proxy)"""
        debug_print("Testing direct connection mode...")
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True
        )
        
        # Mock the YouTube API to avoid actual network calls
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = MOCK_TRANSCRIPT_DATA
            mock_api.return_value = mock_instance
            
            # Test with different URL formats
            for url in TEST_VIDEO_URLS:
                debug_print(f"Testing URL: {url}")
                result = fetcher.get_transcript(url)
                
                assert isinstance(result, list)
                assert len(result) > 0
                assert all('text' in item and 'start' in item and 'duration' in item for item in result)
                
                # Verify API was called with correct parameters
                mock_instance.fetch.assert_called_with('dQw4w9WgXcQ', languages=['en'])
        
        return "Direct connection mode tests passed"
    
    def test_proxy_mode(self):
        """Test fetcher in proxy mode"""
        debug_print("Testing proxy mode...")
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True,
            webshare_username="test_user",
            webshare_password="test_pass"
        )
        
        # Mock the YouTube API and proxy config
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api, \
             patch('transcript_fetcher.WebshareProxyConfig') as mock_proxy_config:
            
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = MOCK_TRANSCRIPT_DATA
            mock_api.return_value = mock_instance
            
            result = fetcher.get_transcript(TEST_VIDEO_URLS[0])
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            # Verify proxy config was used
            mock_proxy_config.assert_called_with(
                proxy_username="test_user",
                proxy_password="test_pass"
            )
            
            # Verify API was called with proxy config
            mock_api.assert_called_with(proxy_config=mock_proxy_config.return_value)
        
        return "Proxy mode tests passed"
    
    def test_caching_functionality(self):
        """Test caching functionality"""
        debug_print("Testing caching functionality...")
        
        # Use a unique cache directory for this test to avoid interference
        cache_test_dir = os.path.join(self.test_cache_dir, "cache_test")
        os.makedirs(cache_test_dir, exist_ok=True)
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=cache_test_dir,
            force=False  # Enable caching
        )
        
        # Mock the YouTube API
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = MOCK_TRANSCRIPT_DATA
            mock_api.return_value = mock_instance
            
            video_url = TEST_VIDEO_URLS[0]
            
            # First call - should fetch from API and cache
            debug_print("First call - should fetch from API")
            result1 = fetcher.get_transcript(video_url)
            assert mock_instance.fetch.call_count == 1
            
            # Second call - should load from cache
            debug_print("Second call - should load from cache")
            result2 = fetcher.get_transcript(video_url)
            assert mock_instance.fetch.call_count == 1  # Should not increase
            
            # Results should be identical
            assert result1 == result2
            
            # Verify cache file exists
            cache_path = fetcher._get_cache_path('dQw4w9WgXcQ')
            assert os.path.exists(cache_path)
            
            # Verify cache content
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            assert cached_data == result1
        
        return "Caching functionality tests passed"
    
    def test_force_refresh(self):
        """Test force refresh functionality"""
        debug_print("Testing force refresh functionality...")
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True  # Force refresh
        )
        
        # Mock the YouTube API
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = MOCK_TRANSCRIPT_DATA
            mock_api.return_value = mock_instance
            
            video_url = TEST_VIDEO_URLS[0]
            
            # Multiple calls with force=True should always fetch from API
            debug_print("Testing multiple calls with force=True")
            for i in range(3):
                result = fetcher.get_transcript(video_url)
                assert isinstance(result, list)
                assert len(result) > 0
            
            # Should have called API 3 times
            assert mock_instance.fetch.call_count == 3
        
        return "Force refresh tests passed"
    
    def test_concurrent_requests(self):
        """Test concurrent request functionality"""
        debug_print("Testing concurrent requests...")
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True,
            webshare_username="test_user",
            webshare_password="test_pass",
            max_concurrent_requests=2
        )
        
        # Mock the YouTube API
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = MOCK_TRANSCRIPT_DATA
            mock_api.return_value = mock_instance
            
            video_url = TEST_VIDEO_URLS[0]
            
            # Test concurrent requests
            debug_print("Testing concurrent requests")
            result = fetcher.get_transcript(video_url)
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            # Verify API was called (should be called at least once)
            assert mock_instance.fetch.call_count >= 1
        
        return "Concurrent requests tests passed"
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        debug_print("Testing error handling...")
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True
        )
        
        # Test 1: Invalid URL - should extract video ID but fail on API call
        debug_print("Testing invalid URL")
        try:
            fetcher.get_transcript("invalid_url")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            # The error message should contain either "Could not extract video ID" or "Failed to download subtitles"
            assert ("Could not extract video ID" in str(e) or "Failed to download subtitles" in str(e))
        
        # Test 2: Empty URL
        debug_print("Testing empty URL")
        try:
            fetcher.get_transcript("")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Could not extract video ID" in str(e)
        
        # Test 3: API failure
        debug_print("Testing API failure")
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api:
            mock_instance = MagicMock()
            mock_instance.fetch.side_effect = Exception("API Error")
            mock_api.return_value = mock_instance
            
            try:
                fetcher.get_transcript(TEST_VIDEO_URLS[0])
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "Failed to download subtitles" in str(e)
        
        return "Error handling tests passed"
    
    def test_generate_flattened(self):
        """Test flattened transcript generation"""
        debug_print("Testing flattened transcript generation...")
        
        fetcher = YouTubeTranscriptFetcher(cache_dir=self.test_cache_dir)
        
        # Test data with dialogue markers
        test_data = [
            {"text": ">> Hello there", "start": 0.0, "duration": 2.0},
            {"text": "How are you?", "start": 2.0, "duration": 2.0},
            {"text": ">> I'm doing well", "start": 4.0, "duration": 2.0},
            {"text": "Thanks for asking", "start": 6.0, "duration": 2.0},
        ]
        
        video_id = "test_video_123"
        
        # Ensure the cache directory structure exists
        video_cache_dir = os.path.join(self.test_cache_dir, video_id)
        os.makedirs(video_cache_dir, exist_ok=True)
        
        result = fetcher.generate_flattened(test_data, video_id)
        
        assert isinstance(result, str)
        assert "Hello there" in result
        assert "I'm doing well" in result
        assert "How are you?" in result
        assert "Thanks for asking" in result
        
        # Verify file was created
        flattened_path = os.path.join(self.test_cache_dir, video_id, 'flattened.txt')
        assert os.path.exists(flattened_path)
        
        # Verify file content
        with open(flattened_path, 'r') as f:
            file_content = f.read()
        assert file_content == result
        
        return "Flattened transcript generation tests passed"
    
    def test_user_agent_rotation(self):
        """Test user agent rotation functionality"""
        debug_print("Testing user agent rotation...")
        
        fetcher = YouTubeTranscriptFetcher(
            cache_dir=self.test_cache_dir,
            force=True
        )
        
        # Mock the YouTube API and random module
        with patch('transcript_fetcher.YouTubeTranscriptApi') as mock_api, \
             patch('random.choice') as mock_random_choice:
            
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = MOCK_TRANSCRIPT_DATA
            mock_api.return_value = mock_instance
            
            # Mock random.choice to return predictable user agents
            mock_random_choice.side_effect = lambda x: x[0]  # Always return first agent
            
            result = fetcher.get_transcript(TEST_VIDEO_URLS[0])
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            # Verify random.choice was called
            mock_random_choice.assert_called()
        
        return "User agent rotation tests passed"
    
    def test_cache_directory_structure(self):
        """Test cache directory structure"""
        debug_print("Testing cache directory structure...")
        
        fetcher = YouTubeTranscriptFetcher(cache_dir=self.test_cache_dir)
        
        # Test cache path generation
        video_id = "test_video_456"
        cache_path = fetcher._get_cache_path(video_id)
        
        expected_path = os.path.join(self.test_cache_dir, video_id, 'transcript.json')
        assert cache_path == expected_path
        
        # Test directory creation
        assert os.path.exists(os.path.dirname(cache_path))
        
        return "Cache directory structure tests passed"
    
    def run_all_tests(self):
        """Run all tests"""
        debug_print("Starting comprehensive test suite for YouTubeTranscriptFetcher")
        debug_print(f"Test cache directory: {self.test_cache_dir}")
        
        try:
            self.setup_test_environment()
            
            # Run all tests
            tests = [
                ("Initialization", self.test_initialization),
                ("Direct Connection Mode", self.test_direct_connection_mode),
                ("Proxy Mode", self.test_proxy_mode),
                ("Caching Functionality", self.test_caching_functionality),
                ("Force Refresh", self.test_force_refresh),
                ("Concurrent Requests", self.test_concurrent_requests),
                ("Error Handling", self.test_error_handling),
                ("Generate Flattened", self.test_generate_flattened),
                ("User Agent Rotation", self.test_user_agent_rotation),
                ("Cache Directory Structure", self.test_cache_directory_structure),
            ]
            
            for test_name, test_func in tests:
                self.run_test(test_name, test_func)
            
            # Print summary
            self.print_test_summary()
            
        finally:
            self.cleanup_test_environment()
    
    def print_test_summary(self):
        """Print test summary"""
        debug_print(f"\n{'='*60}")
        debug_print("TEST SUMMARY")
        debug_print(f"{'='*60}")
        
        passed = sum(1 for result in self.test_results if result['status'] == 'PASSED')
        failed = sum(1 for result in self.test_results if result['status'] == 'FAILED')
        total = len(self.test_results)
        
        debug_print(f"Total tests: {total}")
        debug_print(f"Passed: {passed}")
        debug_print(f"Failed: {failed}")
        debug_print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            debug_print(f"\nFailed tests:")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    debug_print(f"  - {result['name']}: {result.get('error', 'Unknown error')}")
        
        debug_print(f"\n{'='*60}")


def main():
    """Main test runner"""
    debug_print("YouTube Transcript Fetcher Test Suite")
    debug_print("=" * 50)
    
    tester = TestYouTubeTranscriptFetcher()
    tester.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in tester.test_results if result['status'] == 'FAILED')
    sys.exit(failed_tests)


if __name__ == "__main__":
    main()
