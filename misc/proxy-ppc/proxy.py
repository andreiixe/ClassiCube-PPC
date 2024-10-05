from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import urllib.parse
from dateutil import parser
import sys
import time
import threading
import pickle
import os
import json
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

CACHE_FILE = 'cache.pkl'
CACHE_TTL = 2 * 3600
UPDATE_INTERVAL = 24 * 3600
RELEASE_URL = 'https://api.github.com/repos/andreiixe/ClassiCube-PPC/releases/latest'

latest_release = {"release_ts": 0, "release_version": ""}
executor = ThreadPoolExecutor(max_workers=5)

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    cache_lock = threading.Lock()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        query_params = parse_qs(url.query)
        target_url = query_params.get('url', [None])[0]

        if path == '/' and target_url:
            self.handle_forward_request(target_url)
        elif path == '/client/builds.json':
            self.handle_builds_json()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Unsupported request')
            print("Unsupported request")

    def handle_builds_json(self):
        print(f"Handling /client/builds.json request")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        json_data = json.dumps(latest_release)
        self.wfile.write(json_data.encode())
        print("JSON data sent to client.")

    def handle_forward_request(self, target_url):
        print(f"Forwarding request to {target_url}")
        try:
            with requests.get(target_url, stream=True, timeout=(10, 30)) as response:
                self.send_response(response.status_code)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/octet-stream'))
                self.end_headers()

                # Stream response content efficiently
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        try:
                            self.wfile.write(chunk)
                            self.wfile.flush()  # Ensure the chunk is sent immediately
                        except ConnectionAbortedError:
                            print("Connection was aborted by the client.")
                            self.send_response(500)
                            self.end_headers()
                            self.wfile.write(b'Connection aborted by client.')
                            return
                print("Response sent to client.")
        except requests.RequestException as e:
            print(f"Exception occurred: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Error fetching the requested URL')

def cache_get(url):
    print(f"Cache get request for URL: {url}")
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
            cached_time, cached_data = cache.get(url, (0, None))
            if time.time() - cached_time < CACHE_TTL:
                print("Cache valid.")
                return cached_data
            else:
                print("Cache expired.")
    print("Cache miss.")
    return None

def cache_set(url, data):
    print(f"Cache set for URL: {url}")
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
    cache[url] = (time.time(), data)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)
    print("Cache updated.")

def fetch_latest_release():
    global latest_release
    print(f"Fetching latest release from GitHub.")
    try:
        response = requests.get(RELEASE_URL)
        response.raise_for_status()
        release_data = response.json()
        
        tag_name = release_data.get('tag_name', '')
        published_at = release_data.get('published_at', '')
        
        if published_at:
            release_datetime = parser.isoparse(published_at)
            release_ts = release_datetime.timestamp()
        else:
            release_ts = time.time()
        
        latest_release = {
            "release_ts": release_ts,
            "release_version": tag_name
        }
        print(f"Latest release fetched: {latest_release}")
    except requests.RequestException as e:
        print(f"Error fetching release data: {e}")

def refresh_cache():
    while True:
        time.sleep(UPDATE_INTERVAL)
        fetch_latest_release()
        print("Cache refreshed.")

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting proxy server on port {port}...')

    threading.Thread(target=fetch_latest_release, daemon=True).start()
    threading.Thread(target=refresh_cache, daemon=True).start()
    httpd.serve_forever()

if __name__ == '__main__':
    port = 5090
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 8080.")
    
    run(port=port)
