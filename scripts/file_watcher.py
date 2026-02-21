#!/usr/bin/env python3
"""
File Watcher for Auto-reload Web Server
Monitors file changes and triggers server restart.

Usage:
    python scripts/file_watcher.py --port 8080 --dir docs/web
"""

import argparse
import json
import logging
import os
import platform
import signal
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Try to import watchdog
try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("Installing watchdog...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer


# ============================================================
# Error Handling Framework
# ============================================================

class ErrorSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ErrorContext:
    """Context information for error tracking."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error_id: str = field(default_factory=lambda: f"ERR_{int(time.time() * 1000)}")
    component: str = "unknown"
    operation: str = "unknown"
    severity: ErrorSeverity = ErrorSeverity.ERROR
    message: str = ""
    exception_type: str = ""
    exception_message: str = ""
    stack_trace: str = ""
    call_chain: List[str] = field(default_factory=list)
    request_info: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, str] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.system_info = {
            "os": platform.system(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
        }


class ErrorHandler:
    """Enhanced error handler with full stack trace and request tracking."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.error_log_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        self.error_history: List[ErrorContext] = []

    def capture_exception(
        self,
        exc: Exception,
        component: str = "unknown",
        operation: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        request_info: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ) -> ErrorContext:
        """Capture exception with full context."""

        # Get stack trace
        tb = traceback.format_exc()

        # Get call chain
        call_chain = self._extract_call_chain()

        context = ErrorContext(
            component=component,
            operation=operation,
            severity=severity,
            message=str(exc),
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            stack_trace=tb,
            call_chain=call_chain,
            request_info=request_info or {},
            suggestions=suggestions or [],
        )

        self.error_history.append(context)
        self._log_error(context)

        return context

    def _extract_call_chain(self) -> List[str]:
        """Extract the call chain from the current stack."""
        call_chain = []
        for frame_info in traceback.extract_stack()[:-1]:  # Exclude current frame
            call_chain.append(
                f"{frame_info.filename}:{frame_info.lineno} in {frame_info.name}()"
            )
        return call_chain[-10:]  # Keep last 10 calls

    def _log_error(self, context: ErrorContext):
        """Log error to file."""
        log_entry = self._format_error(context)
        with open(self.error_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            f.write("\n" + "=" * 80 + "\n")

    def _format_error(self, context: ErrorContext) -> str:
        """Format error for display and logging."""
        lines = [
            "\n" + "=" * 80,
            f"🔴 ERROR REPORT [{context.error_id}]",
            "=" * 80,
            "",
            f"📅 Timestamp: {context.timestamp}",
            f"🏷️  Severity: {context.severity.value}",
            f"📦 Component: {context.component}",
            f"⚙️  Operation: {context.operation}",
            "",
            "─" * 40,
            "📋 ERROR DETAILS",
            "─" * 40,
            f"Exception Type: {context.exception_type}",
            f"Message: {context.exception_message}",
            "",
            "─" * 40,
            "📚 STACK TRACE",
            "─" * 40,
            context.stack_trace if context.stack_trace else "No stack trace available",
            "",
        ]

        if context.call_chain:
            lines.extend([
                "─" * 40,
                "🔗 CALL CHAIN",
                "─" * 40,
            ])
            for i, call in enumerate(context.call_chain, 1):
                lines.append(f"  {i}. {call}")
            lines.append("")

        if context.request_info:
            lines.extend([
                "─" * 40,
                "🌐 REQUEST INFO",
                "─" * 40,
            ])
            for key, value in context.request_info.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        lines.extend([
            "─" * 40,
            "💻 SYSTEM INFO",
            "─" * 40,
        ])
        for key, value in context.system_info.items():
            lines.append(f"  {key}: {value}")

        if context.suggestions:
            lines.extend([
                "",
                "─" * 40,
                "💡 SUGGESTIONS",
                "─" * 40,
            ])
            for i, suggestion in enumerate(context.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        lines.append("")
        return "\n".join(lines)

    def print_error(self, context: ErrorContext):
        """Print formatted error to console."""
        print(self._format_error(context))

    def get_summary(self) -> str:
        """Get error summary."""
        if not self.error_history:
            return "No errors recorded."

        summary = [
            f"\n📊 Error Summary ({len(self.error_history)} errors)",
            "-" * 40,
        ]

        for ctx in self.error_history[-5:]:  # Last 5 errors
            summary.append(
                f"[{ctx.severity.value}] {ctx.component}.{ctx.operation}: "
                f"{ctx.exception_type}: {ctx.exception_message[:50]}..."
            )

        return "\n".join(summary)


# ============================================================
# Request Tracker
# ============================================================

@dataclass
class RequestInfo:
    """Track HTTP request information."""
    url: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    status_code: int = 0
    response_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


class RequestTracker:
    """Track and log HTTP requests."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.request_log_file = log_dir / f"requests_{datetime.now().strftime('%Y%m%d')}.log"
        self.requests: List[RequestInfo] = []

    def log_request(self, request: RequestInfo):
        """Log request information."""
        self.requests.append(request)
        self._write_request_log(request)

    def _write_request_log(self, request: RequestInfo):
        """Write request to log file."""
        status_emoji = "✅" if 200 <= request.status_code < 300 else "❌"
        log_entry = f"""
{status_emoji} REQUEST [{request.timestamp}]
  URL: {request.url}
  Method: {request.method}
  Params: {json.dumps(request.params, default=str)}
  Status: {request.status_code}
  Response Time: {request.response_time:.3f}s
  Headers: {json.dumps(dict(request.headers), default=str)}
  Error: {request.error or 'None'}
{"-" * 60}
"""
        with open(self.request_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def get_summary(self) -> str:
        """Get request summary."""
        if not self.requests:
            return "No requests recorded."

        success = sum(1 for r in self.requests if 200 <= r.status_code < 300)
        failed = len(self.requests) - success

        summary = [
            f"\n📊 Request Summary ({len(self.requests)} requests)",
            "-" * 40,
            f"  ✅ Success: {success}",
            f"  ❌ Failed: {failed}",
            "",
            "Recent Requests:",
        ]

        for req in self.requests[-5:]:
            status_emoji = "✅" if 200 <= req.status_code < 300 else "❌"
            summary.append(f"  {status_emoji} {req.method} {req.url} [{req.status_code}]")

        return "\n".join(summary)


# ============================================================
# Configure Logging
# ============================================================

def setup_logging(log_dir: Path) -> logging.Logger:
    """Setup enhanced logging with file output."""
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("file_watcher")
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = logging.FileHandler(
        log_dir / f"watcher_{datetime.now().strftime('%Y%m%d')}.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(funcName)s: %(message)s"
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# ============================================================
# Server Manager
# ============================================================

class ServerManager:
    """Manages the HTTP server process lifecycle."""

    def __init__(self, port: int, directory: str, error_handler: ErrorHandler, logger: logging.Logger):
        self.port = port
        self.directory = Path(directory).resolve()
        self.error_handler = error_handler
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.restart_event = Event()
        self.should_run = True
        self.start_count = 0
        self.error_count = 0

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.should_run = False
        self.stop()
        sys.exit(0)

    def start(self) -> bool:
        """Start the HTTP server."""
        if self.process and self.process.poll() is None:
            self.logger.warning("Server already running")
            return True

        self.start_count += 1
        self.logger.info(f"Starting HTTP server (attempt #{self.start_count})")
        self.logger.info(f"Port: {self.port}")
        self.logger.info(f"Directory: {self.directory}")

        try:
            # Verify directory exists
            if not self.directory.exists():
                raise FileNotFoundError(f"Directory not found: {self.directory}")

            # Find available port if current is in use
            if not self._check_port_available(self.port):
                old_port = self.port
                self.port = self._find_available_port()
                self.logger.info(f"Port {old_port} in use, switching to port {self.port}")

            # Start Python HTTP server
            self.process = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(self.port)],
                cwd=str(self.directory),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a moment to check if server started successfully
            time.sleep(1)

            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                error_context = self.error_handler.capture_exception(
                    Exception("Server process exited immediately"),
                    component="ServerManager",
                    operation="start",
                    severity=ErrorSeverity.CRITICAL,
                    request_info={
                        "port": self.port,
                        "directory": str(self.directory),
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": self.process.returncode,
                    },
                    suggestions=[
                        "Check if the port is already in use",
                        "Verify the directory exists and is accessible",
                        "Check Python installation and http.server module",
                    ],
                )
                self.error_handler.print_error(error_context)
                return False

            self.logger.info(f"Server started successfully (PID: {self.process.pid})")
            self.logger.info(f"Access URL: http://localhost:{self.port}")
            
            # Log request info
            request = RequestInfo(
                url=f"http://localhost:{self.port}",
                method="SERVER_START",
                status_code=200,
            )
            
            return True

        except Exception as e:
            self.error_count += 1
            error_context = self.error_handler.capture_exception(
                e,
                component="ServerManager",
                operation="start",
                severity=ErrorSeverity.ERROR,
                request_info={
                    "port": self.port,
                    "directory": str(self.directory),
                },
                suggestions=[
                    "Check if the port is already in use: netstat -ano | findstr :8080",
                    "Try a different port with --port option",
                    "Verify Python installation: python --version",
                ],
            )
            self.error_handler.print_error(error_context)
            return False

    def _check_port_available(self, port: int) -> bool:
        """Check if a specific port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return True
        except OSError:
            return False

    def _find_available_port(self) -> int:
        """Find an available port."""
        import random
        
        # Try random ports in range 10000-65535
        for _ in range(20):
            port = random.randint(10000, 65535)
            if self._check_port_available(port):
                return port
        
        raise OSError("Cannot find available port")

    def stop(self):
        """Stop the HTTP server."""
        if self.process:
            self.logger.info(f"Stopping server (PID: {self.process.pid})")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("Server did not terminate gracefully, killing...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                error_context = self.error_handler.capture_exception(
                    e,
                    component="ServerManager",
                    operation="stop",
                    severity=ErrorSeverity.WARNING,
                )
                self.error_handler.print_error(error_context)
            finally:
                self.process = None
                self.logger.info("Server stopped")

    def restart(self) -> bool:
        """Restart the HTTP server."""
        self.logger.info("Restarting server...")
        self.stop()
        time.sleep(0.5)  # Brief pause before restart
        return self.start()

    def is_running(self) -> bool:
        """Check if server is running."""
        return self.process is not None and self.process.poll() is None

    def check_health(self) -> Dict[str, Any]:
        """Check server health status."""
        return {
            "running": self.is_running(),
            "pid": self.process.pid if self.process else None,
            "port": self.port,
            "directory": str(self.directory),
            "start_count": self.start_count,
            "error_count": self.error_count,
        }


# ============================================================
# File Change Handler
# ============================================================

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system change events."""

    def __init__(
        self,
        server_manager: ServerManager,
        error_handler: ErrorHandler,
        logger: logging.Logger,
        debounce_seconds: float = 1.0,
    ):
        self.server_manager = server_manager
        self.error_handler = error_handler
        self.logger = logger
        self.debounce_seconds = debounce_seconds
        self.last_restart = 0
        self.ignored_extensions = {".pyc", ".pyo", ".swp", ".swo", ".DS_Store", ".git", ".tmp", ".log"}
        self.ignored_dirs = {".git", "__pycache__", "node_modules", ".pids", "logs", ".idea", ".vscode"}
        self.change_count = 0

    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored."""
        path_obj = Path(path)

        # Check extension
        if path_obj.suffix in self.ignored_extensions:
            return True

        # Check directory
        for part in path_obj.parts:
            if part in self.ignored_dirs:
                return True

        return False

    def _debounced_restart(self, event_type: str, path: str):
        """Restart server with debouncing to avoid multiple restarts."""
        current_time = time.time()
        if current_time - self.last_restart < self.debounce_seconds:
            return

        self.last_restart = current_time
        self.change_count += 1

        self.logger.info(f"🔄 File change detected: {event_type}")
        self.logger.info(f"   Path: {path}")
        self.logger.info(f"   Triggering server restart... (change #{self.change_count})")
        
        self.server_manager.restart_event.set()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification event."""
        if event.is_directory:
            return

        if self._should_ignore(event.src_path):
            return

        self._debounced_restart("MODIFIED", event.src_path)

    def on_created(self, event: FileSystemEvent):
        """Handle file creation event."""
        if event.is_directory:
            return

        if self._should_ignore(event.src_path):
            return

        self._debounced_restart("CREATED", event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion event."""
        if event.is_directory:
            return

        if self._should_ignore(event.src_path):
            return

        self._debounced_restart("DELETED", event.src_path)


# ============================================================
# Browser Opener
# ============================================================

def open_browser(url: str, logger: logging.Logger):
    """Open URL in default browser."""
    import webbrowser

    try:
        logger.info(f"Opening browser: {url}")
        webbrowser.open(url)
    except Exception as e:
        logger.warning(f"Could not open browser: {e}")


# ============================================================
# Main Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="File Watcher for Auto-reload Web Server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port number for HTTP server (default: 8765)",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="docs/web",
        help="Directory to serve and watch (default: docs/web)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically",
    )
    parser.add_argument(
        "--watch-extra",
        type=str,
        nargs="*",
        default=[],
        help="Additional directories to watch for changes",
    )
    parser.add_argument(
        "--debounce",
        type=float,
        default=1.0,
        help="Debounce seconds for restart (default: 1.0)",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory for log files (default: logs)",
    )

    args = parser.parse_args()

    # Setup directories
    script_dir = Path(__file__).resolve().parent.parent
    serve_dir = Path(args.dir)
    if not serve_dir.is_absolute():
        serve_dir = script_dir / serve_dir
    log_dir = script_dir / args.log_dir

    # Initialize error handler and logger
    error_handler = ErrorHandler(log_dir)
    logger = setup_logging(log_dir)

    # Validate directory
    if not serve_dir.exists():
        error_context = error_handler.capture_exception(
            FileNotFoundError(f"Directory not found: {serve_dir}"),
            component="Main",
            operation="validate_directory",
            severity=ErrorSeverity.CRITICAL,
            suggestions=[
                f"Create the directory: mkdir {serve_dir}",
                "Check the path specified with --dir option",
            ],
        )
        error_handler.print_error(error_context)
        sys.exit(1)

    # Create server manager
    server = ServerManager(args.port, str(serve_dir), error_handler, logger)

    # Create file change handler
    handler = FileChangeHandler(server, error_handler, logger, debounce_seconds=args.debounce)

    # Setup file observer
    observer = Observer()

    # Watch main directory
    observer.schedule(handler, str(serve_dir), recursive=True)
    logger.info(f"👀 Watching directory: {serve_dir}")

    # Watch additional directories
    for extra_dir in args.watch_extra:
        extra_path = Path(extra_dir)
        if extra_path.exists():
            observer.schedule(handler, str(extra_path), recursive=True)
            logger.info(f"👀 Watching extra directory: {extra_path}")

    # Start observer
    observer.start()
    logger.info("File watcher started")

    # Start server
    if not server.start():
        error_context = error_handler.capture_exception(
            Exception("Failed to start server"),
            component="Main",
            operation="start_server",
            severity=ErrorSeverity.CRITICAL,
        )
        error_handler.print_error(error_context)
        observer.stop()
        sys.exit(1)

    # Open browser
    if not args.no_browser:
        time.sleep(1)  # Wait for server to be ready
        open_browser(f"http://localhost:{server.port}", logger)

    # Main loop
    actual_port = server.port  # May have changed if original port was in use
    print("\n" + "=" * 60)
    print("🚀 Everything About Agent - Web Server Running")
    print("=" * 60)
    print("\n" + "─" * 60)
    print("📍 ACCESS URL (Click or Copy):")
    print("─" * 60)
    print(f"\n    http://localhost:{actual_port}")
    print("\n" + "─" * 60)
    print("\n📝 Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")

    try:
        while server.should_run:
            # Check for restart request
            if server.restart_event.is_set():
                server.restart_event.clear()
                server.restart()

            # Small sleep to prevent busy loop
            time.sleep(0.1)

            # Check server health
            if not server.is_running():
                logger.warning("Server stopped unexpectedly, restarting...")
                server.start()

    except KeyboardInterrupt:
        logger.info("\nShutting down...")

    finally:
        # Print summaries
        print(error_handler.get_summary())
        
        # Cleanup
        observer.stop()
        observer.join()
        server.stop()
        
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
