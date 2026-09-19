"""
Local HTTP server for Google OAuth callback.
Listens on http://localhost:8080/callback for the auth code redirect.
"""

import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from config.config import GOOGLE_OAUTH_PORT


# Shared state between the server and the callback handler
_auth_code = None
_auth_error = None
_server_thread = None
_server = None


class GoogleOAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler for Google OAuth redirect callback."""

    def do_GET(self):
        """Handle GET request from Google's OAuth redirect."""
        global _auth_code, _auth_error

        # Parse the callback URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Extract auth code or error
        if "code" in query_params:
            _auth_code = query_params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
            <head><title>Authentication Successful</title></head>
            <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
                <h1 style="color: #3949AB;">✓ Authentication Successful</h1>
                <p>You have been authenticated with Google. You can close this window.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif "error" in query_params:
            _auth_error = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
            <head><title>Authentication Failed</title></head>
            <body style="font-family: Arial, sans-serif; padding: 50px; text-align: center;">
                <h1 style="color: #d32f2f;">✗ Authentication Failed</h1>
                <p>An error occurred during authentication. Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress server logging."""
        pass


def start_oauth_server() -> bool:
    """
    Start local OAuth callback server (non-blocking).
    Returns True if server started successfully.
    """
    global _auth_code, _auth_error, _server_thread, _server

    _auth_code = None
    _auth_error = None

    def run_server():
        global _server, _auth_code, _auth_error
        try:
            _server = HTTPServer(("localhost", GOOGLE_OAUTH_PORT), GoogleOAuthCallbackHandler)
            # Handle requests with timeout so thread can be interrupted
            _server.timeout = 1.0
            while True:
                _server.handle_request()
                if _auth_code is not None or _auth_error is not None:
                    break
        except Exception as e:
            _auth_error = str(e)
        finally:
            if _server:
                try:
                    _server.server_close()
                except:
                    pass

    # Start server in background thread
    _server_thread = threading.Thread(target=run_server, daemon=True)
    _server_thread.start()

    # Give server a moment to start
    time.sleep(0.5)
    return True


def wait_for_oauth_callback(timeout=600) -> tuple[str | None, str | None]:
    """
    Wait for OAuth callback with timeout.
    Returns (auth_code, error) tuple.
    """
    global _auth_code, _auth_error

    start = time.time()
    while time.time() - start < timeout:
        if _auth_code is not None:
            return _auth_code, None
        if _auth_error is not None:
            return None, _auth_error
        time.sleep(0.1)

    return None, "OAuth callback timeout"


def stop_oauth_server():
    """Stop the OAuth server."""
    global _server
    if _server:
        try:
            _server.server_close()
        except:
            pass
