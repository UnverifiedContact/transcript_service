#!/usr/bin/env python3
"""
YouTube Transcript Fetcher
A class for fetching and caching YouTube transcripts
"""

import os
import json
import concurrent.futures
import time
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from utils import extract_youtube_id

def debug_print(message):
    """Print debug message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    print(f"[{timestamp}] {message}")


class YouTubeTranscriptFetcher:
    """A class to fetch and cache YouTube transcripts"""
    
    def __init__(self, cache_dir="cache", webshare_username=None, webshare_password=None):
        debug_print(f"DEBUG: YouTubeTranscriptFetcher.__init__ called")
        debug_print(f"DEBUG: webshare_username passed: {webshare_username}")
        debug_print(f"DEBUG: webshare_password passed: {'***' if webshare_password else None}")
        self.cache_dir = cache_dir
        self.webshare_username = webshare_username
        self.webshare_password = webshare_password
        debug_print(f"DEBUG: Final webshare_username: {self.webshare_username}")
        debug_print(f"DEBUG: Final webshare_password: {'***' if self.webshare_password else None}")
        self._ensure_cache_dir()
    
    def set_cache_dir(self, cache_dir):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_transcript(self, url):
        debug_print(f"DEBUG: get_transcript called with URL: {url}")
        video_id = extract_youtube_id(url)
        debug_print(f"DEBUG: Extracted video ID: {video_id}")
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        debug_print("DEBUG: Checking cache...")
        cached_data = self._load_from_cache(video_id)
        if cached_data is not None:
            debug_print("DEBUG: Found cached data, returning cached result")
            return cached_data
        debug_print("DEBUG: No cached data found, proceeding to fetch")
        
        # Try concurrent requests if using Webshare proxies, fallback to single request
        debug_print(f"DEBUG: Webshare credentials available: {bool(self.webshare_username and self.webshare_password)}")
        if self.webshare_username and self.webshare_password:
            debug_print("DEBUG: Using Webshare proxies, attempting concurrent requests")
            try:
                transcript_data = self._get_transcript_concurrent(video_id)
                debug_print("DEBUG: Concurrent requests succeeded!")
            except Exception as e:
                debug_print(f"DEBUG: Concurrent requests failed, trying single request: {e}")
                try:
                    debug_print("DEBUG: Attempting single request with Webshare proxies...")
                    transcript_data = self._get_transcript_single(video_id)
                    debug_print("DEBUG: Single request with proxies succeeded!")
                except Exception as e2:
                    debug_print(f"DEBUG: Single request with proxies failed: {e2}")
                    raise ValueError("Failed to download subtitles for this video")
        else:
            debug_print("DEBUG: No Webshare credentials, using single request without proxies")
            try:
                transcript_data = self._get_transcript_single(video_id)
                debug_print("DEBUG: Single request without proxies succeeded!")
            except Exception as e:
                debug_print(f"DEBUG: Single request without proxies failed: {e}")
                raise ValueError("Failed to download subtitles for this video")
        
        transcript_data_dict = [{'text': entry.text, 'start': entry.start, 'duration': entry.duration} for entry in transcript_data]
        
        self._save_to_cache(video_id, transcript_data_dict)
        return transcript_data_dict
    
    def _get_transcript_single(self, video_id):
        """Single transcript fetch attempt"""
        if self.webshare_username and self.webshare_password:
            api = YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=self.webshare_username,
                    proxy_password=self.webshare_password
                )
            )
        else:
            api = YouTubeTranscriptApi()
        return api.fetch(video_id, languages=['en'])
    
    def _get_transcript_concurrent(self, video_id, max_concurrent=3):
        """Try multiple concurrent requests to get transcript"""
        debug_print(f"DEBUG: Starting concurrent requests with {max_concurrent} attempts")
        debug_print(f"DEBUG: Video ID: {video_id}")
        
        import threading
        import queue
        
        # Use a queue to communicate results between threads
        result_queue = queue.Queue()
        stop_event = threading.Event()
        
        def worker_thread(attempt_id):
            """Worker thread that runs a single attempt"""
            if stop_event.is_set():
                debug_print(f"DEBUG: Attempt {attempt_id} cancelled before starting")
                return
                
            try:
                result = self._single_transcript_attempt(video_id, attempt_id)
                if result is not None and not stop_event.is_set():
                    debug_print(f"DEBUG: Attempt {attempt_id} SUCCESS! Got {len(result)} segments")
                    result_queue.put(result)
                    stop_event.set()  # Signal other threads to stop
                else:
                    debug_print(f"DEBUG: Attempt {attempt_id} completed but result was None or cancelled")
            except Exception as e:
                if not stop_event.is_set():
                    debug_print(f"DEBUG: Attempt {attempt_id} FAILED with error: {str(e)[:200]}")
        
        # Start all worker threads
        threads = []
        for i in range(max_concurrent):
            thread = threading.Thread(target=worker_thread, args=(i+1,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        debug_print(f"DEBUG: Waiting for first successful result from {max_concurrent} requests...")
        
        try:
            # Wait for first successful result with timeout
            result = result_queue.get(timeout=15)  # 15 second timeout
            debug_print(f"DEBUG: SUCCESS! Concurrent request succeeded, stopping remaining {max_concurrent-1} attempts")
            return result
        except queue.Empty:
            debug_print(f"DEBUG: Timeout waiting for result from {max_concurrent} concurrent attempts")
            raise ValueError("All concurrent attempts failed or timed out")
        finally:
            # Signal all threads to stop
            stop_event.set()
            
            # Wait a short time for threads to finish gracefully
            for thread in threads:
                thread.join(timeout=1)
    
    
    def _single_transcript_attempt(self, video_id, attempt_id):
        """Single transcript fetch attempt with fresh proxy connection"""
        import time
        import random
        
        debug_print(f"DEBUG: Starting attempt {attempt_id} for video {video_id}")
        
        try:           
            debug_print(f"DEBUG: Attempt {attempt_id} creating fresh API instance...")
            debug_print(f"DEBUG: Attempt {attempt_id} using Webshare username: {self.webshare_username}")
            
            # Create fresh API instance for each attempt
            api = YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=self.webshare_username,
                    proxy_password=self.webshare_password
                )
            )
            
            debug_print(f"DEBUG: Attempt {attempt_id} calling api.fetch()...")
            transcript_data = api.fetch(video_id, languages=['en'])
            debug_print(f"DEBUG: Attempt {attempt_id} SUCCESS! Got {len(transcript_data)} segments")
            return transcript_data
        except Exception as e:
            debug_print(f"DEBUG: Attempt {attempt_id} FAILED with error: {str(e)[:200]}")
            return None
    
    def _get_cache_path(self, video_id):
        """Get the cache file path for a video ID"""
        return os.path.join(self.cache_dir, f'{video_id}.json')
    
    def _save_to_cache(self, video_id, transcript_data):
        """Save transcript data to cache"""
        cache_path = self._get_cache_path(video_id)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
    
    def _load_from_cache(self, video_id):
        """Load transcript data from cache if it exists"""
        cache_path = self._get_cache_path(video_id)
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both old format (wrapper object) and new format (direct array)
                if isinstance(data, dict) and 'transcript_data' in data:
                    return data['transcript_data']
                elif isinstance(data, list):
                    return data
                else:
                    return data
        return None
    
    def generate_flattened(self, transcript_data, video_id):
        import re
        
        if transcript_data is None:
            return ""
        
        regex_pattern = re.compile(r'^\s*>>\s*')
        output_path = os.path.join(self.cache_dir, f'{video_id}_flattened.txt')
        
        flattened_lines = []
        for segment in transcript_data:
            text = segment.get('text', '')
            if regex_pattern.match(text):
                # Remove >> prefix for dialogue lines
                clean_text = regex_pattern.sub('', text)
                flattened_lines.append(clean_text)
            elif text.strip():  # Include all non-empty text segments
                flattened_lines.append(text)
        
        flattened_text = '\n'.join(flattened_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(flattened_text)
        
        return flattened_text
