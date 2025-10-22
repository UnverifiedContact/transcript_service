#!/usr/bin/env python3
"""
Isolation test for YouTube transcript API
Tests DNS resolution and transcript fetching without Flask/eventlet
"""

import socket
import time
from datetime import datetime

def debug_print(message):
    """Print debug message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

def test_dns_resolution():
    """Test basic DNS resolution"""
    debug_print("Testing DNS resolution...")
    try:
        ip = socket.gethostbyname('www.youtube.com')
        debug_print(f"✓ DNS resolution: www.youtube.com -> {ip}")
        return True
    except Exception as e:
        debug_print(f"✗ DNS resolution failed: {e}")
        return False

def test_youtube_transcript_api():
    """Test YouTube transcript API directly"""
    debug_print("Testing YouTube Transcript API...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        debug_print("✓ YouTube Transcript API imported successfully")
        
        # Test with a known video ID that has transcripts
        video_id = 'dQw4w9WgXcQ'  # Rick Roll - known to have transcripts
        debug_print(f"Testing with video ID: {video_id}")
        
        # Test basic fetch
        result = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
        debug_print(f"✓ Transcript fetch successful: Got {len(result)} segments")
        
        # Show first few segments
        for i, segment in enumerate(result[:3]):
            debug_print(f"  Segment {i+1}: {segment.text[:50]}...")
        
        return True
        
    except Exception as e:
        debug_print(f"✗ YouTube Transcript API failed: {e}")
        return False

def test_with_proxy():
    """Test with proxy configuration if available"""
    debug_print("Testing with proxy configuration...")
    
    try:
        import os
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.proxies import WebshareProxyConfig
        
        webshare_username = os.getenv('WEBSHARE_USERNAME')
        webshare_password = os.getenv('WEBSHARE_PASSWORD')
        
        if not webshare_username or not webshare_password:
            debug_print("⚠ No proxy credentials found, skipping proxy test")
            return True
        
        debug_print(f"Testing with Webshare proxy: {webshare_username}")
        
        api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=webshare_username,
                proxy_password=webshare_password
            )
        )
        
        video_id = 'dQw4w9WgXcQ'
        result = api.fetch(video_id, languages=['en'])
        debug_print(f"✓ Proxy transcript fetch successful: Got {len(result)} segments")
        
        return True
        
    except Exception as e:
        debug_print(f"✗ Proxy test failed: {e}")
        return False

def main():
    """Run all isolation tests"""
    debug_print("=== YouTube Transcript API Isolation Test ===")
    debug_print("Testing without Flask/eventlet interference")
    
    tests = [
        ("DNS Resolution", test_dns_resolution),
        ("YouTube Transcript API", test_youtube_transcript_api),
        ("Proxy Configuration", test_with_proxy)
    ]
    
    results = []
    for test_name, test_func in tests:
        debug_print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            debug_print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Small delay between tests
    
    debug_print("\n=== Test Results ===")
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        debug_print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    debug_print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        debug_print("✓ All tests passed - API is working correctly")
    else:
        debug_print("✗ Some tests failed - check the errors above")

if __name__ == "__main__":
    main()
