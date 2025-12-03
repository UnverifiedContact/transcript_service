#!/usr/bin/env python3
"""
YouTube Transcript Service
A Flask microservice for fetching and caching YouTube transcripts
"""

# Eventlet removed - using Gunicorn with thread workers for concurrency

import os
import json
import time
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from transcript_fetcher import YouTubeTranscriptFetcher
from utils import extract_youtube_id

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize the transcript fetcher with settings from environment
# Expand environment variables in CACHE_DIR (e.g., $TMP/cache -> /tmp/cache)
cache_dir = os.path.expandvars(os.getenv('CACHE_DIR', 'cache'))

transcript_fetcher = YouTubeTranscriptFetcher(
    cache_dir=cache_dir,
    webshare_username=os.getenv('WEBSHARE_USERNAME'),
    webshare_password=os.getenv('WEBSHARE_PASSWORD'),
    max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '2'))
)

@app.route('/transcript/<video_id>', methods=['GET'])
def get_transcript(video_id):
    """
    Get transcript for a YouTube video by video ID
    
    Args:
        video_id: YouTube video ID (11 characters)
    
    Returns:
        JSON response with transcript data or error message
    """
    try:
        # Start timing the request
        start_time = time.time()
        
        # Validate video ID format
        if not video_id or len(video_id) != 11:
            return jsonify({
                'error': 'Invalid video ID format',
                'message': 'Video ID must be exactly 11 characters'
            }), 400
        
        # Check for force query parameter (accepts '1' or 'true')
        force = request.args.get('force', '0').lower() in ['1', 'true']
        
        # Check if we have cached data first (unless force refresh is requested)
        if not force:
            cached_data = transcript_fetcher._load_from_cache(video_id)
            if cached_data is not None:
                duration = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
                return jsonify({
                    'video_id': video_id,
                    'transcript': cached_data,
                    'cached': True,
                    'retrieval_duration_ms': duration
                })
        
        # If no cache or force refresh, try to fetch from YouTube
        # Construct a YouTube URL from the video ID
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create a new fetcher instance with force setting for this request
        if force:
            request_fetcher = YouTubeTranscriptFetcher(
                cache_dir=cache_dir,
                webshare_username=os.getenv('WEBSHARE_USERNAME'),
                webshare_password=os.getenv('WEBSHARE_PASSWORD'),
                max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '2')),
                force=True
            )
            transcript_data = request_fetcher.get_transcript(youtube_url)
        else:
            transcript_data = transcript_fetcher.get_transcript(youtube_url)
        
        duration = round((time.time() - start_time) * 1000, 2)  # Convert to milliseconds
        return jsonify({
            'video_id': video_id,
            'transcript': transcript_data,
            'cached': False,
            'retrieval_duration_ms': duration
        })
        
    except ValueError as e:
        return jsonify({
            'error': 'Transcript not available',
            'message': str(e)
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'youtube-transcript-service'
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        'service': 'YouTube Transcript Service',
        'version': '1.0.0',
        'endpoints': {
            'GET /transcript/<video_id>': 'Get transcript for a YouTube video',
            'GET /health': 'Health check',
            'GET /': 'Service information'
        }
    })

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5485))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting YouTube Transcript Service on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)
