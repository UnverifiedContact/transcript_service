#!/usr/bin/env python3
"""
Direct test of videos using Python (bypassing Flask app)
"""

import time
from transcript_fetcher import YouTubeTranscriptFetcher
from utils import debug_print

VIDEOS = [
    "vdZAN4NbEoU",
    "WcUoqVjMLWM",
    "bP_vzHICa4I",
    "RRS0RcEccQM",
    "qByLpjxeNv8",
    "KIY8LvL4Kog"
]

def test_video(video_id, force=False, check_cache_first=False):
    """Test a single video"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Check cache first if requested
    cached = False
    if check_cache_first:
        fetcher_check = YouTubeTranscriptFetcher(cache_dir="test_cache", force=False)
        cached_data = fetcher_check._load_from_cache(video_id)
        cached = cached_data is not None
    
    fetcher = YouTubeTranscriptFetcher(cache_dir="test_cache", force=force)
    
    start_time = time.time()
    try:
        result = fetcher.get_transcript(url)
        elapsed = time.time() - start_time
        return {
            'success': True,
            'elapsed': elapsed,
            'segments': len(result),
            'error': None,
            'cached': cached
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'success': False,
            'elapsed': elapsed,
            'segments': 0,
            'error': str(e)[:200],  # Truncate long errors
            'cached': cached
        }

print("="*70)
print("Testing YouTube Videos - Direct Python Test (WITH FORCE=1)")
print("="*70)
print("Note: Using force=True to bypass cache and fetch from YouTube")
print()

results = []
for video_id in VIDEOS:
    print(f"Testing: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")
    
    # Check if cached first (but don't fetch)
    fetcher_check = YouTubeTranscriptFetcher(cache_dir="test_cache", force=False)
    cached_data = fetcher_check._load_from_cache(video_id)
    was_cached = cached_data is not None
    
    if was_cached:
        print(f"⚠️  Note: This video was previously cached")
    else:
        print(f"ℹ️  Note: This video is NOT in cache - will be a fresh fetch")
    
    # Now test with force=True to bypass cache
    result = test_video(video_id, force=True, check_cache_first=False)
    results.append((video_id, result))
    
    if result['success']:
        cache_status = "CACHED" if was_cached else "FRESH FETCH"
        print(f"✅ SUCCESS in {result['elapsed']:.2f}s - {result['segments']} segments ({cache_status})")
    else:
        print(f"❌ FAILED in {result['elapsed']:.2f}s")
        print(f"   Error: {result['error']}")
    
    print()

print("="*70)
print("SUMMARY")
print("="*70)
print(f"Total videos tested: {len(results)}")
print(f"Successful: {sum(1 for _, r in results if r['success'])}")
print(f"Failed: {sum(1 for _, r in results if not r['success'])}")
print()

print("Detailed Results:")
for video_id, result in results:
    status = "✅" if result['success'] else "❌"
    print(f"{status} {video_id}: {result['elapsed']:.2f}s - ", end="")
    if result['success']:
        print(f"{result['segments']} segments")
    else:
        print(f"Error: {result['error'][:50]}...")
