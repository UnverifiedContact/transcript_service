#!/usr/bin/env python3
"""
YouTube Transcript Fetcher
A class for fetching and caching YouTube transcripts
"""

import os
import json
import concurrent.futures
import time
import socket
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from utils import extract_youtube_id

# Fix DNS resolution for Termux
def fix_dns_resolution():
    """Fix DNS resolution issues in Termux"""
    try:
        # Set DNS servers explicitly
        socket.setdefaulttimeout(30)
        
        # Test DNS resolution
        socket.gethostbyname('www.youtube.com')
        debug_print("DEBUG: DNS resolution test passed")
        return True
    except Exception as e:
        debug_print(f"DEBUG: DNS resolution test failed: {e}")
        return False

def debug_print(message):
    """Print debug message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    print(f"[{timestamp}] {message}")


class YouTubeTranscriptFetcher:
    """A class to fetch and cache YouTube transcripts"""
    
    def __init__(self, cache_dir="cache", webshare_username=None, webshare_password=None, use_webshare=False):
        debug_print(f"DEBUG: YouTubeTranscriptFetcher.__init__ called")
        debug_print(f"DEBUG: webshare_username passed: {webshare_username}")
        debug_print(f"DEBUG: webshare_password passed: {'***' if webshare_password else None}")
        debug_print(f"DEBUG: use_webshare passed: {use_webshare}")
        
        # Test DNS resolution first
        debug_print("DEBUG: Testing DNS resolution...")
        if not fix_dns_resolution():
            debug_print("WARNING: DNS resolution test failed - this may cause issues")
        
        self.cache_dir = cache_dir
        self.use_webshare = use_webshare
        self.webshare_username = webshare_username
        self.webshare_password = webshare_password
        
        # Validate Webshare configuration
        if self.use_webshare:
            if not self.webshare_username or not self.webshare_password:
                raise ValueError("USE_WEBSHARE is enabled but WEBSHARE_USERNAME or WEBSHARE_PASSWORD is missing")
            debug_print(f"DEBUG: Webshare proxy enabled with username: {self.webshare_username}")
        else:
            debug_print(f"DEBUG: Webshare proxy disabled, using direct connections")
        
        debug_print(f"DEBUG: Final webshare_username: {self.webshare_username}")
        debug_print(f"DEBUG: Final webshare_password: {'***' if self.webshare_password else None}")
        debug_print(f"DEBUG: Final use_webshare: {self.use_webshare}")
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
        
        debug_print(f"DEBUG: [{video_id}] Checking cache...")
        cached_data = self._load_from_cache(video_id)
        if cached_data is not None:
            debug_print(f"DEBUG: [{video_id}] Found cached data, returning cached result")
            return cached_data
        debug_print(f"DEBUG: [{video_id}] No cached data found, proceeding to fetch")
        
        # Try concurrent requests if using Webshare proxies, fallback to single request
        debug_print(f"DEBUG: [{video_id}] Webshare enabled: {self.use_webshare}")
        if self.use_webshare:
            debug_print(f"DEBUG: [{video_id}] Using Webshare proxies, attempting concurrent requests")
            try:
                transcript_data = self._get_transcript_concurrent(video_id)
                debug_print(f"DEBUG: [{video_id}] Concurrent requests succeeded!")
            except Exception as e:
                debug_print(f"DEBUG: [{video_id}] Concurrent requests failed, trying single request: {e}")
                try:
                    debug_print(f"DEBUG: [{video_id}] Attempting single request with Webshare proxies...")
                    transcript_data = self._get_transcript_single(video_id)
                    debug_print(f"DEBUG: [{video_id}] Single request with proxies succeeded!")
                except Exception as e2:
                    debug_print(f"DEBUG: [{video_id}] Single request with proxies failed: {e2}")
                    raise ValueError("Failed to download subtitles for this video")
        else:
            debug_print(f"DEBUG: [{video_id}] No Webshare credentials, using single request without proxies")
            try:
                transcript_data = self._get_transcript_single(video_id)
                debug_print(f"DEBUG: [{video_id}] Single request without proxies succeeded!")
            except Exception as e:
                debug_print(f"DEBUG: [{video_id}] Single request without proxies failed: {e}")
                raise ValueError("Failed to download subtitles for this video")
        
        # Handle both old format (list) and new format (FetchedTranscript object)
        if hasattr(transcript_data, 'snippets'):
            # New format: FetchedTranscript object with snippets attribute
            transcript_data_dict = [{'text': snippet.text, 'start': snippet.start, 'duration': snippet.duration} for snippet in transcript_data.snippets]
        else:
            # Old format: list of transcript segments
            transcript_data_dict = [{'text': entry.text, 'start': entry.start, 'duration': entry.duration} for entry in transcript_data]
        
        self._save_to_cache(video_id, transcript_data_dict)
        return transcript_data_dict
    
    def _get_transcript_single(self, video_id):
        """Single transcript fetch attempt with user-agent rotation and enhanced headers"""
        import random
        import time
        
        # User-agent rotation to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Enhanced headers to mimic real browser requests
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        debug_print(f"DEBUG: [{video_id}] Using User-Agent: {headers['User-Agent'][:50]}...")
        
        # Test DNS resolution before attempting requests
        debug_print(f"DEBUG: [{video_id}] Testing DNS resolution before request...")
        try:
            socket.gethostbyname('www.youtube.com')
            debug_print(f"DEBUG: [{video_id}] DNS resolution test passed")
        except Exception as dns_error:
            debug_print(f"DEBUG: [{video_id}] DNS resolution test failed: {dns_error}")
            debug_print(f"DEBUG: [{video_id}] Attempting to fix DNS resolution...")
            
            # Try to fix DNS resolution
            try:
                socket.setdefaulttimeout(30)
                socket.gethostbyname('www.youtube.com')
                debug_print(f"DEBUG: [{video_id}] DNS resolution fixed")
            except Exception as fix_error:
                debug_print(f"DEBUG: [{video_id}] DNS resolution fix failed: {fix_error}")
                raise ValueError(f"DNS resolution failed: {fix_error}")
        
        # Try with proxy first, then fallback to direct connection
        if self.use_webshare:
            try:
                debug_print(f"DEBUG: [{video_id}] Attempting with Webshare proxy...")
                api = YouTubeTranscriptApi(
                    proxy_config=WebshareProxyConfig(
                        proxy_username=self.webshare_username,
                        proxy_password=self.webshare_password
                    )
                )
                result = api.fetch(video_id, languages=['en'])
                debug_print(f"DEBUG: [{video_id}] Proxy request succeeded!")
                return result
            except Exception as proxy_error:
                debug_print(f"DEBUG: [{video_id}] Proxy request failed: {proxy_error}")
                debug_print(f"DEBUG: [{video_id}] Falling back to direct connection...")
                
                # Add a small delay before retry
                time.sleep(1)
                
                try:
                    api = YouTubeTranscriptApi()
                    result = api.fetch(video_id, languages=['en'])
                    debug_print(f"DEBUG: [{video_id}] Direct connection succeeded!")
                    return result
                except Exception as direct_error:
                    debug_print(f"DEBUG: [{video_id}] Direct connection also failed: {direct_error}")
                    raise direct_error
        else:
            api = YouTubeTranscriptApi()
            return api.fetch(video_id, languages=['en'])
    
    def _get_transcript_concurrent(self, video_id, max_concurrent=2):
        """Try multiple concurrent requests to get transcript"""
        debug_print(f"DEBUG: [{video_id}] Starting concurrent requests with {max_concurrent} attempts")
        
        import threading
        import queue
        
        # Use a queue to communicate results between threads
        result_queue = queue.Queue()
        stop_event = threading.Event()
        
        def worker_thread(attempt_id):
            """Worker thread that runs a single attempt"""
            if stop_event.is_set():
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} cancelled before starting")
                return
                
            try:
                result = self._single_transcript_attempt(video_id, attempt_id)
                if result is not None and not stop_event.is_set():
                    debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} SUCCESS! Got {len(result)} segments")
                    result_queue.put(result)
                    stop_event.set()  # Signal other threads to stop
                else:
                    debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} completed but result was None or cancelled")
            except Exception as e:
                if not stop_event.is_set():
                    debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} FAILED with error: {str(e)[:200]}")
        
        # Start all worker threads
        threads = []
        for i in range(max_concurrent):
            thread = threading.Thread(target=worker_thread, args=(i+1,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        debug_print(f"DEBUG: [{video_id}] Waiting for first successful result from {max_concurrent} requests...")
        
        try:
            # Wait for first successful result with timeout
            result = result_queue.get(timeout=15)  # 15 second timeout
            debug_print(f"DEBUG: [{video_id}] SUCCESS! Concurrent request succeeded, stopping remaining {max_concurrent-1} attempts")
            return result
        except queue.Empty:
            debug_print(f"DEBUG: [{video_id}] Timeout waiting for result from {max_concurrent} concurrent attempts")
            raise ValueError("All concurrent attempts failed or timed out")
        finally:
            # Signal all threads to stop
            stop_event.set()
            
            # Wait a short time for threads to finish gracefully
            for thread in threads:
                thread.join(timeout=1)
    
    
    def _get_current_ip(self):
        """Get the current external IP address for proxy verification"""
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', timeout=5)
            return response.json().get('ip', 'unknown')
        except:
            try:
                import requests
                response = requests.get('https://api.ipify.org', timeout=5)
                return response.text.strip()
            except:
                return 'unknown'

    def _single_transcript_attempt(self, video_id, attempt_id):
        """Single transcript fetch attempt with fresh proxy connection and backoff"""
        import time
        import random
        
        debug_print(f"DEBUG: [{video_id}] Starting attempt {attempt_id}")
        
        # Add exponential backoff with jitter
        base_delay = 2 ** attempt_id  # 2, 4, 8 seconds
        jitter = random.uniform(0, 1)  # Add randomness
        delay = base_delay + jitter
        
        debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} waiting {delay:.2f}s before request...")
        time.sleep(delay)
        
        try:           
            debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} creating fresh API instance...")
            debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} using Webshare username: {self.webshare_username}")
            
            # User-agent rotation for each attempt
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
            ]
            
            selected_ua = random.choice(user_agents)
            debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} using User-Agent: {selected_ua[:50]}...")
            
            # Try with proxy first, then fallback to direct connection
            try:
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} trying with Webshare proxy...")
                api = YouTubeTranscriptApi(
                    proxy_config=WebshareProxyConfig(
                        proxy_username=self.webshare_username,
                        proxy_password=self.webshare_password
                    )
                )
                
                # Get IP address to verify proxy rotation
                current_ip = self._get_current_ip()
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} using proxy IP: {current_ip}")
                
                transcript_data = api.fetch(video_id, languages=['en'])
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} SUCCESS with proxy IP {current_ip}! Got {len(transcript_data)} segments")
                return transcript_data
            except Exception as proxy_error:
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} proxy failed: {str(proxy_error)[:100]}...")
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} falling back to direct connection...")
                
                # Add a small delay before retry
                time.sleep(0.5)
                
                api = YouTubeTranscriptApi()
                
                # Get IP address for direct connection
                current_ip = self._get_current_ip()
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} using direct IP: {current_ip}")
                
                transcript_data = api.fetch(video_id, languages=['en'])
                debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} SUCCESS with direct IP {current_ip}! Got {len(transcript_data)} segments")
                return transcript_data
                
        except Exception as e:
            debug_print(f"DEBUG: [{video_id}] Attempt {attempt_id} FAILED with error: {str(e)[:200]}")
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
