#!/bin/bash
# Termux DNS Resolution Diagnosis Script
# READ-ONLY diagnostic script to identify DNS issues in Termux

echo "=== Termux DNS Resolution Diagnosis ==="
echo "This script will diagnose DNS resolution issues in Termux"
echo "READ-ONLY - No changes will be made to your system"
echo

# Check if running in Termux (read-only notice, no prompt)
if [ ! -d "/data/data/com.termux" ]; then
    echo "WARNING: This script is designed for Termux. You may not be running in Termux."
    echo "Proceeding in read-only diagnostic mode."
fi

echo "1. Checking Termux environment..."
echo "Termux data directory: /data/data/com.termux"
ls -la /data/data/com.termux 2>/dev/null | head -5 || echo "Cannot access Termux directory"

echo
echo "2. Checking current DNS configuration..."
echo "Checking /etc/resolv.conf:"
if [ -f "/etc/resolv.conf" ]; then
    cat /etc/resolv.conf
else
    echo "File /etc/resolv.conf does not exist"
fi

echo
echo "Checking system DNS configuration:"
getprop | grep dns 2>/dev/null || echo "No DNS properties found"

echo
echo "3. Testing basic network connectivity..."
echo "Testing ping to Google DNS:"
ping -c 2 8.8.8.8 2>/dev/null && echo "✓ Ping to 8.8.8.8 successful" || echo "✗ Ping to 8.8.8.8 failed"

echo
echo "Testing ping to Cloudflare DNS:"
ping -c 2 1.1.1.1 2>/dev/null && echo "✓ Ping to 1.1.1.1 successful" || echo "✗ Ping to 1.1.1.1 failed"

echo
echo "4. Testing DNS resolution tools..."
echo "Testing nslookup:"
which nslookup >/dev/null 2>&1 && echo "✓ nslookup available" || echo "✗ nslookup not available"

if which nslookup >/dev/null 2>&1; then
    echo "Testing DNS resolution with nslookup:"
    nslookup www.youtube.com 2>/dev/null && echo "✓ DNS resolution working" || echo "✗ DNS resolution failed"
fi

echo
echo "Testing dig:"
which dig >/dev/null 2>&1 && echo "✓ dig available" || echo "✗ dig not available"

if which dig >/dev/null 2>&1; then
    echo "Testing DNS resolution with dig:"
    dig www.youtube.com +short 2>/dev/null && echo "✓ DNS resolution working" || echo "✗ DNS resolution failed"
fi

echo
echo "5. Testing Python DNS resolution..."
python3 -c "
import socket
import sys

print('Testing socket.gethostbyname:')
try:
    ip = socket.gethostbyname('www.youtube.com')
    print(f'✓ Python DNS resolution: www.youtube.com -> {ip}')
except Exception as e:
    print(f'✗ Python DNS resolution failed: {e}')

print('Testing socket.getaddrinfo:')
try:
    result = socket.getaddrinfo('www.youtube.com', 443)
    print(f'✓ Python getaddrinfo: Found {len(result)} addresses')
except Exception as e:
    print(f'✗ Python getaddrinfo failed: {e}')
"

echo
echo "6. Testing HTTP requests..."
python3 -c "
import requests
import sys

print('Testing requests.get to YouTube:')
try:
    response = requests.get('https://www.youtube.com', timeout=10)
    print(f'✓ HTTP requests working: Status {response.status_code}')
except Exception as e:
    print(f'✗ HTTP requests failed: {e}')

print('Testing requests.get to Google:')
try:
    response = requests.get('https://www.google.com', timeout=10)
    print(f'✓ HTTP requests to Google: Status {response.status_code}')
except Exception as e:
    print(f'✗ HTTP requests to Google failed: {e}')
"

echo
echo "7. Checking network interfaces..."
echo "Available network interfaces:"
ip addr show 2>/dev/null || ifconfig 2>/dev/null || echo "Cannot determine network interfaces"

echo
echo "8. Checking routing table..."
echo "Routing table:"
ip route show 2>/dev/null || route -n 2>/dev/null || echo "Cannot determine routing table"

echo
echo "9. Testing YouTube Transcript API specifically..."
python3 -c "
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print('✓ YouTube Transcript API import successful')
    
    # Test with a known video ID
    print('Testing YouTube Transcript API fetch:')
    result = YouTubeTranscriptApi().fetch('dQw4w9WgXcQ', languages=['en'])
    print(f'✓ YouTube Transcript API working: Got {len(result)} segments')
except Exception as e:
    print(f'✗ YouTube Transcript API failed: {e}')
"

echo
echo "10. Checking Termux packages..."
echo "Installed packages related to networking:"
pkg list-installed | grep -E "(dns|net|curl|wget)" 2>/dev/null || echo "No networking packages found"

echo
echo "=== Diagnosis Complete ==="
echo "This was a READ-ONLY diagnosis. No changes were made to your system."
echo "Review the output above to identify DNS resolution issues."
