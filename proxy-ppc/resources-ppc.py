from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import urllib.parse
import sys
import time
import threading
import pickle
import os

CACHE_FILE = 'cache.pkl'
CACHE_TTL = 2 * 3600  # refresh 2 hours

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # Check if starts
        if path.startswith('/resources-ppc/'):
            # Strip the proxy
            actual_path = path[len('/resources-ppc/'):]
            target_url = f'https://resources.download.minecraft.net/{actual_path}'

            # Check cache
            cached_response = cache_get(target_url)
            if cached_response:
                response, headers = cached_response
            else:
                # Forward the request to the target URL
                try:
                    response = requests.get(target_url)
                    headers = response.headers
                    cache_set(target_url, (response, headers))
                except requests.RequestException as e:
                    self.send_error(500, f"Internal Server Error: {e}")
                    return

            self.send_response(response.status_code)
            for header, value in headers.items():
                if header.lower() != 'content-encoding':  # Avoid forwarding 
                    self.send_header(header, value)
            self.end_headers()

            self.wfile.write(response.content)
        else:
            self.send_error(404, "Not Found")

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
        # Purge cache
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        print("Cache refreshed.")

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'PPC Resources started in {port}')
    threading.Thread(target=refresh_cache, daemon=True).start()
    httpd.serve_forever()

if __name__ == '__main__':
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port 8080")
    
    run(port=port)

