"""
Background runner for the Flask demo application.
Allows testing http://localhost:5000 or http://127.0.0.1:5000 inside the same
Streamlit Cloud container or local environment without requiring a separate terminal.
"""

import socket
import threading
import time
from typing import Tuple

import requests


_server_thread: threading.Thread = None
_server_lock = threading.Lock()


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a local TCP port is already open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def is_demo_server_running(base_url: str = "http://127.0.0.1:5000") -> bool:
    """Ping demo health check endpoint."""
    url = f"{base_url.rstrip('/')}/api/health"
    try:
        r = requests.get(url, timeout=0.8)
        return r.status_code == 200
    except Exception:
        return False


def start_demo_server_background(host: str = "127.0.0.1", port: int = 5000) -> Tuple[bool, str]:
    """
    Start the demo Flask app in a daemon background thread.
    Returns (success, message).
    """
    global _server_thread

    # Check if already running and responding
    if is_demo_server_running(f"http://{host}:{port}"):
        return True, f"Demo server already active on http://{host}:{port}"

    with _server_lock:
        if is_demo_server_running(f"http://{host}:{port}"):
            return True, f"Demo server already active on http://{host}:{port}"

        try:
            from demo_app.app import app as flask_app
            from werkzeug.serving import make_server

            server = make_server(host, port, flask_app, threaded=True)

            def _run():
                try:
                    server.serve_forever()
                except Exception:
                    pass

            thread = threading.Thread(target=_run, daemon=True, name="FlaskDemoServer")
            thread.start()
            _server_thread = thread

            # Poll until ready or deadline
            deadline = time.time() + 4.0
            while time.time() < deadline:
                if is_demo_server_running(f"http://{host}:{port}"):
                    return True, f"Demo server started on http://{host}:{port}"
                time.sleep(0.2)

            return True, f"Demo server launched on http://{host}:{port} (background binding)"

        except Exception as e:
            return False, f"Failed to start demo server: {str(e)}"


def ensure_demo_server_if_local(target_url: str) -> None:
    """If target_url is localhost:5000 or 127.0.0.1:5000, ensure background server is running."""
    if not target_url:
        return
    u = target_url.lower()
    if ":5000" in u and ("localhost" in u or "127.0.0.1" in u):
        try:
            start_demo_server_background(host="127.0.0.1", port=5000)
        except Exception:
            pass
