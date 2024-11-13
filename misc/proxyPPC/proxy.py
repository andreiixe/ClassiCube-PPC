from flask import Flask, request, jsonify, Response, render_template_string
import requests
import threading
import time
from dateutil import parser

app = Flask(__name__)

RELEASE_URL = 'https://api.github.com/repos/andreiixe/ClassiCube-PPC/releases/latest'
latest_release = {"release_ts": 0, "release_version": ""}
active_downloads = {}

STATUS_PAGE = """
<!doctype html>
<html>
<head>
    <title>Status PPCProxy ClassiCube</title>
    <style>
        .progress-container {
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-bar {
            height: 25px;
            background-color: #76c7c0;
            text-align: center;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Status</h1>
    <p>Last release: ClassiCube-PPC {{ latest_release['release_version'] }}</p>
    <p>Proxy PPC version: 1.6</p>
    
    <h2>Download Now: {{ active_downloads|length }} users</h2>
    <div class="progress-container">
        <div class="progress-bar" style="width: {{ active_downloads|length * 10 }}%;">
            {{( active_downloads|length) }}
        </div>
    </div>
    
    <h2>Ping curent: {{ current_ping }} ms</h2>
    <div class="progress-container">
        <div class="progress-bar" style="width: {{ adjusted_ping }}%;">
            {{(current_ping // 10) }}{{(10 - (current_ping // 10)) }}
        </div>
    </div>
</body>
</html>
"""

@app.route('/client/builds.json', methods=['GET'])
def handle_builds_json():
    return jsonify(latest_release)

@app.route('/', methods=['GET'])
def handle_forward_request():
    target_url = request.args.get('url')
    if target_url:
        ip = request.remote_addr
        active_downloads[ip] = time.time()  
        
        try:
            response = requests.get(target_url, timeout=(5, 10))
            response.raise_for_status()
            
            return Response(
                response.content,
                content_type=response.headers.get('Content-Type', 'application/octet-stream'),
                status=response.status_code
            )
        except requests.RequestException as e:
            return Response(f"Error fetching the requested URL: {e}", status=500)
    return Response("Unsupported request", status=400)

@app.route('/status', methods=['GET'])
def status_page():
    global active_downloads  
    current_ping = 50  
    adjusted_ping = min(current_ping, 100)
    
    timeout = 10  
    current_time = time.time()
    active_downloads_filtered = {ip: ts for ip, ts in active_downloads.items() if current_time - ts < timeout}
    
    active_downloads = active_downloads_filtered
    
    return render_template_string(
        STATUS_PAGE,
        latest_release=latest_release,
        active_downloads=active_downloads,
        current_ping=current_ping,
        adjusted_ping=adjusted_ping 
    )

def fetch_latest_release():
    global latest_release
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
    except requests.RequestException as e:
        print(f"Error fetching release data: {e}")

if __name__ == '__main__':
    threading.Thread(target=fetch_latest_release, daemon=True).start()
    port = 5090
    app.run(host='0.0.0.0', port=port)
