# YouTube Transcript Service

A standalone Flask microservice for fetching and caching YouTube video transcripts.

## Features

- **RESTful API**: Simple HTTP endpoints for transcript retrieval
- **Caching**: Automatic caching of transcripts to avoid repeated API calls
- **Proxy Support**: Optional Webshare proxy support for enhanced reliability
- **Error Handling**: Comprehensive error handling with meaningful responses
- **Health Checks**: Built-in health check endpoint for monitoring

## API Endpoints

### GET /transcript/{video_id}
Retrieve transcript for a YouTube video by its video ID.

**Parameters:**
- `video_id` (string): 11-character YouTube video ID

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "transcript": [
    {
      "text": "Never gonna give you up",
      "start": 0.0,
      "duration": 3.0
    }
  ],
  "cached": false,
  "message": "Transcript fetched from YouTube"
}
```

**Error Response:**
```json
{
  "error": "Transcript not available",
  "message": "Failed to download subtitles for this video"
}
```

### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "youtube-transcript-service"
}
```

### GET /
Service information and available endpoints.

## Installation

1. Clone or copy this service to your desired location
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The service can be configured using environment variables:

- `WEBSHARE_USERNAME`: Username for Webshare proxy (optional)
- `WEBSHARE_PASSWORD`: Password for Webshare proxy (optional)
- `FLASK_HOST`: Host to bind the service to (default: 0.0.0.0)
- `FLASK_PORT`: Port to run the service on (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)

## Running the Service

### Development Mode
```bash
python app.py
```

### Production Mode
```bash
FLASK_DEBUG=False python app.py
```

The service will start on `http://localhost:5000` by default.

## Usage Examples

### Using curl
```bash
# Get transcript for a video
curl http://localhost:5000/transcript/dQw4w9WgXcQ

# Health check
curl http://localhost:5000/health
```

### Using Python requests
```python
import requests

# Get transcript
response = requests.get('http://localhost:5000/transcript/dQw4w9WgXcQ')
transcript_data = response.json()

if response.status_code == 200:
    print(f"Transcript: {transcript_data['transcript']}")
else:
    print(f"Error: {transcript_data['error']}")
```

## Cache Structure

The service uses a local file-based cache with the following structure:
```
cache/
├── {video_id}/
│   └── transcript.json
```

Cached transcripts are automatically loaded on subsequent requests for the same video ID.

## Error Handling

The service handles various error conditions:

- **400 Bad Request**: Invalid video ID format
- **404 Not Found**: Transcript not available for the video
- **500 Internal Server Error**: Unexpected server errors

## Dependencies

- Flask: Web framework
- youtube-transcript-api: YouTube transcript fetching
- Standard Python libraries (os, json, re, time, datetime, etc.)

## Notes

- This service is designed to be completely standalone
- It mimics the cache structure of the original rebait system
- Webshare proxy support is optional but recommended for production use
- The service will be moved to its own repository in the future
