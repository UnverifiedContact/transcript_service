#!/usr/bin/env python3
"""
Gunicorn startup script for YouTube Transcript Service
Handles environment setup and starts the production server
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Setup environment variables and paths"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Set Python path to include current directory
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

def get_gunicorn_command():
    """Build the gunicorn command with appropriate settings"""
    # Get configuration from environment - optimized for Helio G99 mobile deployment
    host = os.getenv('HOST', '0.0.0.0')
    port = os.getenv('PORT', '5485')
    workers = os.getenv('GUNICORN_WORKERS', '4')  # Conservative for mobile: 4 workers for Helio G99
    log_level = os.getenv('GUNICORN_LOG_LEVEL', 'info')
    reload = os.getenv('GUNICORN_RELOAD', '0') in ('1', 'true', 'yes', 'on')
    
    # Build command - optimized for mobile deployment
    cmd = [
        'gunicorn',
        '--bind', f'{host}:{port}',
        '--workers', workers,
        '--worker-class', 'eventlet',  # Async workers for better mobile performance
        '--timeout', '30',
        '--keepalive', '2',
        '--max-requests', '500',  # Lower for mobile memory management
        '--max-requests-jitter', '50',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', log_level,
        '--proc-name', 'youtube-transcript-service',
        '--preload-app'
    ]
    
    # Add reload option for development
    if reload:
        cmd.append('--reload')
    
    # Add the Flask app
    cmd.extend(['app:app'])
    
    return cmd

def main():
    """Main entry point"""
    print("Starting YouTube Transcript Service with Gunicorn...")
    
    # Setup environment
    setup_environment()
    
    # Get gunicorn command
    cmd = get_gunicorn_command()
    
    # Print configuration
    print(f"Configuration (Helio G99 Mobile Optimized):")
    print(f"  Host: {os.getenv('HOST', '0.0.0.0')}")
    print(f"  Port: {os.getenv('PORT', '5485')}")
    print(f"  Workers: {os.getenv('GUNICORN_WORKERS', '4')}")
    print(f"  Worker Class: eventlet (async)")
    print(f"  Reload: {os.getenv('GUNICORN_RELOAD', 'False')}")
    print(f"  Log Level: {os.getenv('GUNICORN_LOG_LEVEL', 'info')}")
    print()
    
    # Start gunicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting gunicorn: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)

if __name__ == '__main__':
    main()
