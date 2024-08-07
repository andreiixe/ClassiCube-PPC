from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import urllib.parse
import sys
import time
import threading
import pickle
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

CACHE_FILE = 'cache.pkl'
CACHE_TTL = 2 * 3600  # 2 hours in seconds

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    cache_lock = threading.Lock()  # Lock for cache access

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path.startswith('/resources-ppc/'):
            # Handle requests to Minecraft resource URLs
            actual_path = path[len('/resources-ppc/'):]
            target_url = f'https://resources.download.minecraft.net/{actual_path}'
            self.handle_minecraft_cache(target_url)
        else:
            # Handle requests to other URLs
            query_params = parse_qs(url.query)
            target_url = query_params.get('url', [None])[0]

            if not target_url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing "url" query parameter')
                return
            
            self.forward_request(target_url)

    def handle_minecraft_cache(self, target_url):
        with self.cache_lock:  # Ensure thread-safe cache access
            cached_response = cache_get(target_url)
        
        if cached_response:
            response, headers = cached_response
        else:
            try:
                response = requests.get(target_url)
                headers = response.headers
                with self.cache_lock:  # Ensure thread-safe cache access
                    cache_set(target_url, (response, headers))
            except requests.RequestException as e:
                self.send_error(500, f"Internal Server Error: {e}")
                return
        
        self.send_response(response.status_code)
        for header, value in headers.items():
            if header.lower() != 'content-encoding':
                self.send_header(header, value)
        self.end_headers()
        self.wfile.write(response.content)

    def forward_request(self, target_url):
        try:
            response = requests.get(target_url, stream=True)
            self.send_response(response.status_code)
            self.send_header('Content-Type', response.headers.get('Content-Type', 'application/octet-stream'))
            self.end_headers()

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())

def cache_get(url):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
            cached_time, cached_data = cache.get(url, (0, None))
            if time.time() - cached_time < CACHE_TTL:
                return cached_data
    return None

def cache_set(url, data):
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
    cache[url] = (time.time(), data)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

def refresh_cache():
    while True:
        time.sleep(CACHE_TTL)
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        print("Cache refreshed.")

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting proxy server on port {port}...')

    # Use ThreadPoolExecutor for managing threads
    with ThreadPoolExecutor() as executor:
        threading.Thread(target=refresh_cache, daemon=True).start()
        httpd.serve_forever()

if __name__ == '__main__':
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 8080.")
    
    run(port=port)