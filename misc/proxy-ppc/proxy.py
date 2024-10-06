from flask import Flask, request, jsonify, Response
import requests
import threading
import time
import pickle
import os
from dateutil import parser

app = Flask(__name__)

CACHE_FILE = 'cache.pkl'
CACHE_TTL = 2 * 3600
UPDATE_INTERVAL = 24 * 3600
RELEASE_URL = 'https://api.github.com/repos/andreiixe/ClassiCube-PPC/releases/latest'

latest_release = {"release_ts": 0, "release_version": ""}
cache_lock = threading.Lock()

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

@app.route('/client/builds.json', methods=['GET'])
def handle_builds_json():
    print("Handling /client/builds.json request")
    return jsonify(latest_release)

@app.route('/', methods=['GET'])
def handle_forward_request():
    target_url = request.args.get('url')
    if target_url:
        print(f"Forwarding request to {target_url}")
        try:
            response = requests.get(target_url, stream=True, timeout=(10, 30))
            return Response(response.iter_content(chunk_size=8192),
                            content_type=response.headers.get('Content-Type', 'application/octet-stream'),
                            status=response.status_code)
        except requests.RequestException as e:
            print(f"Exception occurred: {e}")
            return Response(f"Error fetching the requested URL: {e}", status=500)
    return Response("Unsupported request", status=400)

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

if __name__ == '__main__':
    threading.Thread(target=fetch_latest_release, daemon=True).start()
    threading.Thread(target=refresh_cache, daemon=True).start()
    
    port = 5090
    app.run(host='0.0.0.0', port=port)
