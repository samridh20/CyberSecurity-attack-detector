#!/usr/bin/env python3
"""
Simple HTTP server for testing NIDS detection.
"""

import http.server
import socketserver
import threading
import time

class TestHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Test Server</h1><p>This is a test server for NIDS testing.</p></body></html>")
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Received POST data: {len(post_data)} bytes".encode())

def start_test_server(port=8080):
    """Start a simple HTTP server for testing."""
    with socketserver.TCPServer(("", port), TestHTTPHandler) as httpd:
        print(f"Test server running on http://localhost:{port}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nServer stopped")

if __name__ == "__main__":
    start_test_server()