#!/usr/bin/env python3
"""
CORS proxy for web_video_server with proper MJPEG streaming support.
Adds CORS headers to allow cross-origin access from Cloudflare tunnel.
"""

import http.server
import socketserver
import urllib.request
import socket

PROXY_PORT = 8081
VIDEO_SERVER_URL = "http://localhost:8080"

class CORSVideoProxyHandler(http.server.BaseHTTPRequestHandler):
    timeout = 60
    
    def add_cors_headers(self):
        """Add CORS headers to allow cross-origin requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Expose-Headers', '*')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.add_cors_headers()
        self.end_headers()
    
    def do_HEAD(self):
        """Handle HEAD requests"""
        self.send_response(200)
        self.add_cors_headers()
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--BoundaryString')
        self.end_headers()
    
    def do_GET(self):
        """Proxy GET requests to web_video_server with CORS headers"""
        try:
            # Strip /camera prefix if present (Cloudflare tunnel preserves the path)
            path = self.path
            if path.startswith('/camera'):
                path = path[7:]  # Remove '/camera' prefix
            if not path.startswith('/'):
                path = '/' + path
            
            url = f"{VIDEO_SERVER_URL}{path}"
            print(f"[CameraProxy] Forwarding: {self.path} -> {url}")
            
            req = urllib.request.Request(url)
            
            # Set timeout for connection
            response = urllib.request.urlopen(req, timeout=10)
            
            # Send success response with CORS headers
            self.send_response(200)
            self.add_cors_headers()
            
            # Copy relevant headers from upstream
            content_type = response.headers.get('Content-Type', 'multipart/x-mixed-replace')
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            # Stream data continuously (for MJPEG)
            try:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            
        except urllib.error.URLError as e:
            self.send_error_response(502, f"Upstream connection failed: {e}")
        except socket.timeout:
            self.send_error_response(504, "Upstream timeout")
        except Exception as e:
            self.send_error_response(500, f"Proxy error: {e}")
    
    def send_error_response(self, code, message):
        """Send error response with CORS headers"""
        self.send_response(code)
        self.add_cors_headers()
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode())
    
    def log_message(self, format, *args):
        print(f"[CameraProxy] {self.address_string()} - {args[0]}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    print(f"Camera CORS Proxy starting on port {PROXY_PORT}...")
    print(f"Forwarding to {VIDEO_SERVER_URL}")
    
    with ThreadedHTTPServer(("", PROXY_PORT), CORSVideoProxyHandler) as httpd:
        print(f"Camera CORS Proxy running on http://0.0.0.0:{PROXY_PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down proxy...")
