import re
import os
import time
from urllib.parse import urlparse, parse_qs


def extract_youtube_id(value: str) -> str | None:
    if not value:
        return None
    value = value.strip()
    
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    
    parsed = urlparse(value)
    
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        m = re.match(r"^/(embed|shorts)/([^/?#&]+)", parsed.path)
        if m:
            return m.group(2)
    
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    
    return None


def read_file_content(file_path: str) -> str:
    """Read content from a file as string"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file_content(file_path: str, content: str) -> None:
    """Write content to a file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


class Timer:
    """Simple timer context manager for benchmarking operations"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
    
    def get_duration(self) -> str:
        """Get duration formatted in a human-readable way"""
        return format_duration(self.duration or 0.0)


def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way with time unit suffix"""
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        minutes = int(seconds // 60)
        remaining_seconds = int(round(seconds % 60))
        return f"{minutes}:{remaining_seconds:02d}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}s"
        else:
            return f"{minutes:02d}:{remaining_seconds:02d}s"


def format_video_duration(seconds: float) -> str:
    """Format video duration in HH:MM:SS format without time unit suffix"""
    if seconds < 60:
        minutes = int(seconds // 60)
        remaining_seconds = int(round(seconds % 60))
        return f"{minutes}:{remaining_seconds:02d}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
        else:
            return f"{minutes:02d}:{remaining_seconds:02d}"
