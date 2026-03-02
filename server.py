#!/usr/bin/env python3
"""
Simple static file server with a tiny JSON API for drivers/users (mock).
Run: python server.py
"""
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8000

# Mock data (small subset)
MOCK = {
    "drivers": [
        {"id": "DRV-1001", "name": "Kavita Choudhary", "vehicleNumber": "MH-20-AW-8254", "rating": 4.9},
        {"id": "DRV-1002", "name": "Suresh Verma", "vehicleNumber": "MH-79-BF-7237", "rating": 4.9}
    ],
    "users": [
        {"id": "USR-5001", "name": "John Doe", "email": "john@example.com", "balance": 500}
    ]
}

class APIRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            self.handle_api(parsed.path)
        else:
            # Serve static files from current directory
            return SimpleHTTPRequestHandler.do_GET(self)

    def handle_api(self, path):
        if path == '/api/drivers':
            self.respond_json(MOCK['drivers'])
        elif path == '/api/users':
            self.respond_json(MOCK['users'])
        elif path.startswith('/api/driver/'):
            did = path.split('/')[-1]
            item = next((d for d in MOCK['drivers'] if d['id'] == did), None)
            self.respond_json(item or {})
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode('utf-8'))

    def respond_json(self, obj):
        payload = json.dumps(obj)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(payload.encode('utf-8'))


def get_mock_data():
    return MOCK


def run(port=PORT):
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    addr = ('', port)
    httpd = HTTPServer(addr, APIRequestHandler)
    print(f"Serving on http://localhost:{port} (static + /api/drivers /api/users)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down')
        httpd.server_close()


if __name__ == '__main__':
    run()
