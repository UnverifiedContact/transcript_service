#!/usr/bin/env python3
"""
Test script to verify timeout functionality works correctly
"""

import time
import sys
from transcript_fetcher import YouTubeTranscriptFetcher
from utils import debug_print

def test_timeout_mechanism():
    """Test that timeout mechanism works and errors are returned quickly"""
    print("\n" + "="*60)
    print("Testing Timeout Mechanism")
    print("="*60)
    
    # Create a fetcher instance
    fetcher = YouTubeTranscriptFetcher(
        cache_dir="test_cache",
        force=True
    )
    
    print(f"API_TIMEOUT is set to: {fetcher.API_TIMEOUT} seconds")
    
    # Test 1: Test with an invalid video ID that should fail quickly
    print("\n--- Test 1: Invalid Video ID (should fail quickly) ---")
    invalid_video_id = "INVALID_VIDEO_ID_12345"
    start_time = time.time()
    
    try:
        result = fetcher.get_transcript(f"https://www.youtube.com/watch?v={invalid_video_id}")
        print(f"ERROR: Should have raised an exception, but got result: {result}")
        return False
    except ValueError as e:
        elapsed = time.time() - start_time
        print(f"✅ Got ValueError as expected: {e}")
        print(f"⏱️  Time taken: {elapsed:.2f} seconds")
        
        # Should fail quickly (within timeout period, ideally much faster)
        if elapsed > fetcher.API_TIMEOUT + 5:
            print(f"❌ ERROR: Took {elapsed:.2f} seconds, which exceeds timeout of {fetcher.API_TIMEOUT} seconds")
            return False
        elif elapsed > 60:
            print(f"⚠️  WARNING: Took {elapsed:.2f} seconds, which is quite slow but within limits")
        else:
            print(f"✅ Timeout working correctly - error returned in {elapsed:.2f} seconds")
    
    # Test 2: Test timeout wrapper directly with a mock that hangs
    print("\n--- Test 2: Direct Timeout Wrapper Test ---")
    from unittest.mock import MagicMock, patch
    
    # Create a mock API that hangs (simulates slow network)
    class HangingAPI:
        def fetch(self, video_id, languages):
            # Simulate a hang by sleeping longer than timeout
            time.sleep(fetcher.API_TIMEOUT + 5)
            return []
    
    hanging_api = HangingAPI()
    start_time = time.time()
    
    try:
        result = fetcher._fetch_with_timeout(hanging_api, "test_video", timeout=5)
        print(f"ERROR: Should have timed out, but got result: {result}")
        return False
    except TimeoutError as e:
        elapsed = time.time() - start_time
        print(f"✅ Got TimeoutError as expected: {e}")
        print(f"⏱️  Time taken: {elapsed:.2f} seconds")
        
        # Should timeout around 5 seconds (with some tolerance)
        if elapsed < 4 or elapsed > 7:
            print(f"⚠️  WARNING: Timeout took {elapsed:.2f} seconds, expected ~5 seconds")
        else:
            print(f"✅ Timeout wrapper working correctly - timed out in {elapsed:.2f} seconds")
    
    # Test 3: Test that a real API error is returned immediately (not after timeout)
    print("\n--- Test 3: Real API Error (should fail immediately) ---")
    from youtube_transcript_api._errors import TranscriptsDisabled
    
    # Use a video ID that likely doesn't exist or has transcripts disabled
    # This should fail quickly with an API error, not timeout
    test_video_id = "ZZZZZZZZZZZ"  # Invalid format
    start_time = time.time()
    
    try:
        result = fetcher.get_transcript(f"https://www.youtube.com/watch?v={test_video_id}")
        print(f"ERROR: Should have raised an exception")
        return False
    except ValueError as e:
        elapsed = time.time() - start_time
        print(f"✅ Got ValueError as expected: {e}")
        print(f"⏱️  Time taken: {elapsed:.2f} seconds")
        
        # Should fail quickly, not wait for full timeout
        if elapsed > fetcher.API_TIMEOUT:
            print(f"⚠️  WARNING: Took {elapsed:.2f} seconds, which is close to timeout")
        else:
            print(f"✅ Error returned quickly in {elapsed:.2f} seconds (not waiting for timeout)")
    
    print("\n" + "="*60)
    print("All timeout tests completed!")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        success = test_timeout_mechanism()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
