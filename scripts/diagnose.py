#!/usr/bin/env python3
"""
Diagnostic Tool for Everything About Agent
Provides detailed error analysis and troubleshooting steps.

Usage:
    python scripts/diagnose.py [--fix]
"""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


# ============================================================
# Color Output
# ============================================================

class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    MAGENTA = "\033[0;35m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        """Disable colors for non-TTY output."""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.RED = ""
        cls.BLUE = ""
        cls.CYAN = ""
        cls.MAGENTA = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.RESET = ""


# ============================================================
# Error Reporting
# ============================================================

@dataclass
class DiagnosticError:
    """Represents a diagnostic error with full context."""
    error_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    severity: str = "ERROR"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    category: str = "unknown"
    component: str = "unknown"
    message: str = ""
    details: str = ""
    stack_trace: str = ""
    call_chain: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    related_urls: List[str] = field(default_factory=list)


class ErrorReporter:
    """Enhanced error reporting with stack traces and context."""

    def __init__(self):
        self.errors: List[DiagnosticError] = []

    def add_error(
        self,
        message: str,
        category: str = "unknown",
        component: str = "unknown",
        severity: str = "ERROR",
        details: str = "",
        exc: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None,
    ) -> DiagnosticError:
        """Add a new diagnostic error."""

        error_id = f"ERR_{len(self.errors) + 1:04d}"

        # Capture stack trace if exception provided
        stack_trace = ""
        call_chain = []
        if exc:
            stack_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            for frame in traceback.extract_tb(exc.__traceback__):
                call_chain.append(f"{frame.filename}:{frame.lineno} in {frame.name}()")

        error = DiagnosticError(
            error_id=error_id,
            severity=severity,
            category=category,
            component=component,
            message=message,
            details=details,
            stack_trace=stack_trace,
            call_chain=call_chain,
            suggestions=suggestions or [],
        )

        self.errors.append(error)
        return error

    def print_error(self, error: DiagnosticError):
        """Print formatted error to console."""
        severity_colors = {
            "DEBUG": Colors.DIM,
            "INFO": Colors.BLUE,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "CRITICAL": Colors.MAGENTA,
        }
        color = severity_colors.get(error.severity, Colors.RESET)

        print(f"\n{Colors.BOLD}{color}{'━' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{color}  {error.severity}: {error.message}{Colors.RESET}")
        print(f"{Colors.BOLD}{color}{'━' * 60}{Colors.RESET}")
        print(f"{Colors.DIM}  ID: {error.error_id}{Colors.RESET}")
        print(f"{Colors.DIM}  Category: {error.category} | Component: {error.component}{Colors.RESET}")
        print(f"{Colors.DIM}  Time: {error.timestamp}{Colors.RESET}")

        if error.details:
            print(f"\n{Colors.CYAN}  Details:{Colors.RESET}")
            print(f"    {error.details}")

        if error.stack_trace:
            print(f"\n{Colors.RED}  Stack Trace:{Colors.RESET}")
            for line in error.stack_trace.split("\n")[:20]:  # Limit to 20 lines
                print(f"    {line}")
            if len(error.stack_trace.split("\n")) > 20:
                print(f"    {Colors.DIM}... (truncated){Colors.RESET}")

        if error.call_chain:
            print(f"\n{Colors.BLUE}  Call Chain:{Colors.RESET}")
            for i, call in enumerate(error.call_chain[-5:], 1):  # Last 5 calls
                print(f"    {i}. {call}")

        if error.suggestions:
            print(f"\n{Colors.GREEN}  Suggestions:{Colors.RESET}")
            for i, suggestion in enumerate(error.suggestions, 1):
                print(f"    {i}. {suggestion}")

        print()

    def print_summary(self):
        """Print summary of all errors."""
        if not self.errors:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ No errors found!{Colors.RESET}\n")
            return

        # Group by severity
        by_severity: Dict[str, List[DiagnosticError]] = {}
        for error in self.errors:
            by_severity.setdefault(error.severity, []).append(error)

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  ERROR SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")

        for severity in ["CRITICAL", "ERROR", "WARNING", "INFO"]:
            if severity in by_severity:
                errors = by_severity[severity]
                color = {"CRITICAL": Colors.MAGENTA, "ERROR": Colors.RED, "WARNING": Colors.YELLOW, "INFO": Colors.BLUE}.get(severity, Colors.RESET)
                print(f"{color}{Colors.BOLD}{severity}:{Colors.RESET} {len(errors)} issue(s)")
                for error in errors:
                    print(f"  • [{error.error_id}] {error.category}: {error.message[:50]}{'...' if len(error.message) > 50 else ''}")


# ============================================================
# Diagnostic Checks
# ============================================================

class DiagnosticReport:
    """Generates diagnostic report for the project."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[str, Any] = {}
        self.reporter = ErrorReporter()
        self.recommendations: List[str] = []

    def print_header(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")

    def print_result(self, name: str, status: str, message: str = ""):
        """Print diagnostic result with status indicator."""
        status_config = {
            "OK": (Colors.GREEN, "✅"),
            "PASS": (Colors.GREEN, "✅"),
            "WARNING": (Colors.YELLOW, "⚠️"),
            "ERROR": (Colors.RED, "❌"),
            "INFO": (Colors.BLUE, "ℹ️"),
            "SKIP": (Colors.DIM, "⏭️"),
        }
        color, icon = status_config.get(status, (Colors.RESET, "•"))
        print(f"  {icon} {name}: {color}{status}{Colors.RESET}")
        if message:
            print(f"     {Colors.DIM}└─ {message}{Colors.RESET}")

    def check_system_info(self) -> Dict:
        """Check system information."""
        self.print_header("System Information")

        try:
            info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "python_version": platform.python_version(),
                "python_path": sys.executable,
                "architecture": platform.architecture()[0],
                "hostname": platform.node(),
                "processor": platform.processor(),
                "working_directory": str(Path.cwd()),
            }

            self.print_result("Operating System", "INFO", f"{info['os']} {info['os_release']}")
            self.print_result("Python Version", "INFO", info["python_version"])
            self.print_result("Python Path", "INFO", str(info["python_path"]))
            self.print_result("Architecture", "INFO", info["architecture"])
            self.print_result("Processor", "INFO", info["processor"] or "Unknown")
            self.print_result("Working Directory", "INFO", info["working_directory"])

            # Check Python version compatibility
            py_version = tuple(map(int, platform.python_version().split(".")[:2]))
            if py_version < (3, 8):
                self.reporter.add_error(
                    "Python version too old",
                    category="system",
                    component="python",
                    severity="ERROR",
                    details=f"Current version: {info['python_version']}, required: >= 3.8",
                    suggestions=["Upgrade Python to version 3.8 or higher"],
                )

            return info

        except Exception as e:
            self.reporter.add_error(
                "Failed to get system info",
                category="system",
                component="diagnostic",
                severity="WARNING",
                exc=e,
            )
            return {}

    def check_port_availability(self, port: int = 8080) -> Tuple[bool, Optional[str]]:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind(("", port))
                return True, None
        except OSError as e:
            return False, str(e)

    def check_ports(self) -> Dict:
        """Check port availability and usage."""
        self.print_header("Port Status")

        # Check commonly used ports
        ports_to_check = [11434, 8000, 8080, 8001]  # Backend services
        port_status = {}

        for port in ports_to_check:
            available, error = self.check_port_availability(port)
            port_info = self._get_port_process_info(port)

            if available:
                self.print_result(f"Port {port}", "OK", "Available")
                port_status[port] = {"status": "available"}
            else:
                process_info = port_info or "Unknown process"
                self.print_result(f"Port {port}", "WARNING", f"In use: {process_info}")
                port_status[port] = {"status": "in_use", "process": process_info}

                # Add error for backend service ports
                if port in [11434, 8000]:
                    self.reporter.add_error(
                        f"Port {port} is occupied",
                        category="network",
                        component="port",
                        severity="WARNING",
                        details=process_info,
                        suggestions=[
                            f"Stop the process using port {port}",
                            f"Use a different port by modifying the startup script",
                            f"Run: netstat -ano | findstr :{port} (Windows) or lsof -i :{port} (Linux)",
                        ],
                    )

        return port_status

    def _get_port_process_info(self, port: int) -> Optional[str]:
        """Get detailed process info using the port."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    f'netstat -ano | findstr ":{port}" | findstr LISTENING',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout:
                    lines = result.stdout.strip().split("\n")
                    if lines:
                        parts = lines[0].split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            # Get process name
                            proc_result = subprocess.run(
                                f'tasklist /FI "PID eq {pid}" /NH /FO CSV',
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            if proc_result.stdout:
                                import csv
                                reader = csv.reader([proc_result.stdout.strip()])
                                row = next(reader, None)
                                if row and len(row) >= 1:
                                    proc_name = row[0].strip('"')
                                    # Get command line
                                    cmd_result = subprocess.run(
                                        f'wmic process where processid={pid} get commandline /value 2>nul',
                                        shell=True,
                                        capture_output=True,
                                        text=True,
                                        timeout=5,
                                    )
                                    cmdline = ""
                                    if cmd_result.stdout:
                                        for line in cmd_result.stdout.split("\n"):
                                            if line.startswith("CommandLine="):
                                                cmdline = line.split("=", 1)[1].strip()[:60]
                                    return f"{proc_name} (PID: {pid}) - {cmdline}..."
                    return f"PID: {pid}"
            else:
                result = subprocess.run(
                    f"lsof -i :{port} -t",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.stdout:
                    pid = result.stdout.strip().split("\n")[0]
                    proc_result = subprocess.run(
                        f"ps -p {pid} -o comm=,args=",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if proc_result.stdout:
                        parts = proc_result.stdout.strip().split(None, 1)
                        proc_name = parts[0] if parts else "Unknown"
                        cmdline = parts[1][:50] if len(parts) > 1 else ""
                        return f"{proc_name} (PID: {pid}) - {cmdline}"
        except Exception as e:
            self.reporter.add_error(
                "Failed to get port process info",
                category="network",
                component="port",
                severity="DEBUG",
                exc=e,
            )
        return None

    def check_processes(self) -> Dict:
        """Check running Python processes."""
        self.print_header("Process Status")

        processes = []

        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    'tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout:
                    import csv
                    for row in csv.reader(result.stdout.strip().split("\n")):
                        if row and len(row) >= 5:
                            processes.append(
                                {
                                    "name": row[0].strip('"'),
                                    "pid": row[1].strip('"'),
                                    "memory": row[4].strip('"').replace(",", ""),
                                }
                            )
            else:
                result = subprocess.run(
                    "ps aux | grep python | grep -v grep",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        parts = line.split(None, 10)
                        if len(parts) >= 2:
                            processes.append(
                                {
                                    "name": parts[-1] if len(parts) > 10 else "python",
                                    "pid": parts[1],
                                    "memory": parts[3],
                                }
                            )

            if processes:
                print(f"  Found {len(processes)} Python process(es):\n")
                for proc in processes[:10]:  # Show max 10 processes
                    mem_info = f" (Memory: {int(proc.get('memory', 0)) // 1024}MB)" if proc.get("memory", "").isdigit() else ""
                    name = proc.get("name", "python")[:40]
                    print(f"    • {name} (PID: {proc['pid']}){mem_info}")
                if len(processes) > 10:
                    print(f"    {Colors.DIM}... and {len(processes) - 10} more{Colors.RESET}")
            else:
                self.print_result("Python Processes", "OK", "No Python processes running")

        except Exception as e:
            self.reporter.add_error(
                "Failed to check processes",
                category="system",
                component="process",
                severity="WARNING",
                exc=e,
            )

        return {"count": len(processes), "processes": processes[:20]}

    def check_logs(self) -> Dict:
        """Check and analyze log files."""
        self.print_header("Log Analysis")

        logs_dir = self.project_root / "logs"
        log_info = {"exists": False, "files": [], "recent_errors": [], "total_size": 0}

        if not logs_dir.exists():
            self.print_result("Logs Directory", "WARNING", "Not found (will be created on first run)")
            self.recommendations.append("Run start.bat/sh to create logs directory")
            return log_info

        log_info["exists"] = True
        self.print_result("Logs Directory", "OK", str(logs_dir))

        # Get log files
        log_files = list(logs_dir.glob("*.log"))
        log_info["files"] = [str(f) for f in log_files]
        log_info["total_size"] = sum(f.stat().st_size for f in log_files if f.exists())

        if not log_files:
            self.print_result("Log Files", "WARNING", "No log files found")
            return log_info

        print(f"\n  {Colors.BOLD}Log Files:{Colors.RESET}")
        for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
            size = log_file.stat().st_size
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_str = f"{size // 1024}KB" if size > 1024 else f"{size}B"
            print(f"    • {log_file.name} ({size_str}, modified: {mtime})")

            # Check for errors
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    error_count = content.lower().count("error")
                    if error_count > 0:
                        log_info["recent_errors"].append({"file": log_file.name, "count": error_count})
                        if error_count > 5:
                            self.print_result(f"  {log_file.name}", "WARNING", f"Contains {error_count} error(s)")
            except Exception:
                pass

        # Show total size
        total_mb = log_info["total_size"] / (1024 * 1024)
        print(f"\n  Total log size: {total_mb:.2f} MB")

        if total_mb > 100:
            self.recommendations.append("Consider cleaning up old log files to save disk space")

        return log_info

    def check_dependencies(self) -> Dict:
        """Check project dependencies."""
        self.print_header("Dependencies")

        deps = {"installed": [], "missing": [], "outdated": []}

        required_packages = [
            ("langchain", "LangChain Core"),
            ("langchain_community", "LangChain Community"),
            ("langchain_ollama", "LangChain Ollama"),
            ("langchain_openai", "LangChain OpenAI"),
            ("ollama", "Ollama SDK"),
            ("pydantic", "Pydantic"),
            ("loguru", "Loguru Logger"),
            ("watchdog", "File Watcher"),
            ("requests", "HTTP Requests"),
            ("yaml", "PyYAML"),
        ]

        for module_name, display_name in required_packages:
            try:
                # Try to import the module
                import_name = module_name if module_name != "yaml" else "yaml"
                result = subprocess.run(
                    [sys.executable, "-c", f"import {import_name}; print(getattr({import_name}, '__version__', 'installed'))"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    version = result.stdout.strip() or "installed"
                    self.print_result(display_name, "OK", f"v{version}")
                    deps["installed"].append({"name": display_name, "version": version})
                else:
                    self.print_result(display_name, "ERROR", "Not installed")
                    deps["missing"].append(display_name)
                    self.reporter.add_error(
                        f"Missing dependency: {display_name}",
                        category="dependency",
                        component="python",
                        severity="ERROR",
                        suggestions=[f"Install: pip install {module_name}"],
                    )
            except Exception as e:
                self.print_result(display_name, "ERROR", str(e)[:50])
                deps["missing"].append(display_name)

        # Check pip itself
        try:
            pip_result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if pip_result.returncode == 0:
                print(f"\n  pip: {pip_result.stdout.strip()}")
        except Exception:
            self.print_result("pip", "ERROR", "pip not available")

        if deps["missing"]:
            missing_str = " ".join(deps["missing"])
            self.recommendations.append(f"Install missing dependencies: pip install {missing_str}")

        return deps

    def check_configuration(self) -> Dict:
        """Check project configuration files."""
        self.print_header("Configuration")

        config_status = {}

        configs = [
            ("configs/models.yaml", "Model Configuration", True),
            ("configs/backends/ollama.yaml", "Ollama Backend Config", True),
            ("configs/backends/vllm.yaml", "vLLM Backend Config", False),
            ("configs/app.yaml", "Application Config", True),
            ("pyproject.toml", "Project Definition", True),
            ("CODEBUDDY.md", "Project Guidance", False),
        ]

        for config_path, name, required in configs:
            full_path = self.project_root / config_path
            if full_path.exists():
                size = full_path.stat().st_size
                self.print_result(name, "OK", f"{config_path} ({size} bytes)")
                config_status[config_path] = True

                # Validate YAML files
                if config_path.endswith(".yaml"):
                    try:
                        import yaml
                        with open(full_path, "r", encoding="utf-8") as f:
                            yaml.safe_load(f)
                        self.print_result(f"  {name} Syntax", "OK", "Valid YAML")
                    except Exception as e:
                        self.print_result(f"  {name} Syntax", "ERROR", str(e)[:50])
                        self.reporter.add_error(
                            f"Invalid YAML in {name}",
                            category="config",
                            component="yaml",
                            severity="ERROR",
                            details=str(e),
                            suggestions=[f"Fix syntax error in {config_path}"],
                        )
            else:
                if required:
                    self.print_result(name, "ERROR", f"Missing: {config_path}")
                    self.reporter.add_error(
                        f"Missing config file: {name}",
                        category="config",
                        component="file",
                        severity="ERROR" if required else "WARNING",
                        suggestions=[f"Create {config_path} or restore from backup"],
                    )
                else:
                    self.print_result(name, "SKIP", f"Optional: {config_path}")
                config_status[config_path] = False

        return config_status

    def check_backend_connectivity(self) -> Dict:
        """Check backend connectivity."""
        self.print_header("Backend Connectivity")

        backends = {
            "ollama": {"url": "http://localhost:11434", "name": "Ollama", "endpoint": "/api/tags"},
            "vllm": {"url": "http://localhost:8000", "name": "vLLM", "endpoint": "/v1/models"},
        }

        connectivity = {}

        for backend_id, info in backends.items():
            try:
                import urllib.request
                import urllib.error

                url = f"{info['url']}{info['endpoint']}"
                req = urllib.request.Request(url, method="GET")
                
                start_time = datetime.now()
                with urllib.request.urlopen(req, timeout=5) as response:
                    status = response.status
                    response_time = (datetime.now() - start_time).total_seconds()
                    data = response.read().decode("utf-8")[:100]  # First 100 chars

                if status == 200:
                    self.print_result(info["name"], "OK", f"{info['url']} - {response_time:.2f}s")
                    connectivity[backend_id] = {"status": "connected", "response_time": response_time}
                else:
                    self.print_result(info["name"], "WARNING", f"{info['url']} - Status: {status}")
                    connectivity[backend_id] = {"status": "error", "code": status}

            except urllib.error.URLError as e:
                self.print_result(info["name"], "WARNING", f"{info['url']} - Connection refused")
                connectivity[backend_id] = {"status": "unavailable"}
            except Exception as e:
                self.print_result(info["name"], "WARNING", f"{info['url']} - {str(e)[:40]}")
                connectivity[backend_id] = {"status": "error", "error": str(e)}

        if not any(c.get("status") == "connected" for c in connectivity.values()):
            self.recommendations.append("Start a backend service (Ollama or vLLM) to use AI features")
            self.recommendations.append("Ollama: Download from https://ollama.ai and run 'ollama serve'")
            self.recommendations.append("vLLM: Run 'python -m vllm.entrypoints.openai.api_server --model <model_name>'")

        return connectivity

    def check_pid_files(self) -> Dict:
        """Check PID files for running services."""
        self.print_header("Service PID Files")

        pid_dir = self.project_root / ".pids"
        pid_status = {"exists": False, "files": {}}

        if not pid_dir.exists():
            self.print_result("PID Directory", "INFO", "Not found (no services tracked)")
            return pid_status

        pid_status["exists"] = True

        for pid_file in pid_dir.glob("*.pid"):
            try:
                pid = pid_file.read_text().strip()
                is_running = self._check_process_running(pid)
                status = "Running" if is_running else "Stopped"
                status_code = "OK" if is_running else "WARNING"

                self.print_result(pid_file.stem, status_code, f"PID {pid} - {status}")
                pid_status["files"][pid_file.stem] = {"pid": pid, "running": is_running}

                if not is_running:
                    self.recommendations.append(f"Clean up stale PID file: {pid_file.name}")
            except Exception as e:
                self.print_result(pid_file.stem, "ERROR", str(e)[:50])

        return pid_status

    def _check_process_running(self, pid: str) -> bool:
        """Check if process with given PID is running."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    f'tasklist /FI "PID eq {pid}" /NH',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return pid in result.stdout
            else:
                result = subprocess.run(
                    ["ps", "-p", pid],
                    capture_output=True,
                    timeout=5,
                )
                return result.returncode == 0
        except Exception:
            return False

    def check_web_files(self) -> Dict:
        """Check web frontend files."""
        self.print_header("Web Frontend Files")

        web_dir = self.project_root / "docs" / "web"
        web_status = {"exists": False, "files": {}}

        if not web_dir.exists():
            self.print_result("Web Directory", "ERROR", "Not found")
            self.reporter.add_error(
                "Web directory not found",
                category="web",
                component="files",
                severity="ERROR",
                suggestions=["Check if docs/web directory exists"],
            )
            return web_status

        web_status["exists"] = True
        self.print_result("Web Directory", "OK", str(web_dir))

        # Check key files
        key_files = [
            "index.html",
            "pattern.html",
            "css/styles.css",
            "js/app.js",
            "js/pattern-data.js",
            "js/chat.js",
            "js/diagram.js",
        ]

        for file_name in key_files:
            file_path = web_dir / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                self.print_result(file_name, "OK", f"{size} bytes")
                web_status["files"][file_name] = True
            else:
                self.print_result(file_name, "ERROR", "Missing")
                web_status["files"][file_name] = False
                self.reporter.add_error(
                    f"Missing web file: {file_name}",
                    category="web",
                    component="files",
                    severity="WARNING",
                )

        return web_status

    def generate_summary(self):
        """Generate diagnostic summary with recommendations."""
        self.print_header("Diagnostic Summary")

        # Print error summary
        self.reporter.print_summary()

        # Print recommendations
        if self.recommendations:
            print(f"\n{Colors.BOLD}{Colors.GREEN}📋 Recommendations:{Colors.RESET}")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")

        # Print quick fix commands
        print(f"\n{Colors.BOLD}{Colors.BLUE}🔧 Quick Fix Commands:{Colors.RESET}")
        print(f"  {Colors.DIM}# Fix missing dependencies:{Colors.RESET}")
        print("  pip install -e .")
        print()
        print(f"  {Colors.DIM}# Stop all services:{Colors.RESET}")
        print("  .\\start.bat   # Select option 7")
        print()
        print(f"  {Colors.DIM}# Start web frontend:{Colors.RESET}")
        print("  .\\start.bat   # Select option 5 or 6")
        print()
        print(f"  {Colors.DIM}# View error logs:{Colors.RESET}")
        print("  .\\start.bat   # Select option 10, then type 'errors'")
        print()

    def save_report(self, output_path: Optional[Path] = None):
        """Save diagnostic report to JSON file."""
        if output_path is None:
            output_path = self.project_root / "logs" / f"diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "results": self.results,
            "errors": [
                {
                    "id": e.error_id,
                    "severity": e.severity,
                    "category": e.category,
                    "component": e.component,
                    "message": e.message,
                    "details": e.details,
                    "suggestions": e.suggestions,
                }
                for e in self.reporter.errors
            ],
            "recommendations": self.recommendations,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n{Colors.GREEN}📄 Report saved to: {output_path}{Colors.RESET}")

    def run_full_diagnosis(self):
        """Run all diagnostic checks."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 60}")
        print("  Everything About Agent - Diagnostic Tool")
        print(f"{'═' * 60}{Colors.RESET}")
        print(f"{Colors.DIM}  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.DIM}  Project: {self.project_root}{Colors.RESET}")

        self.results["system_info"] = self.check_system_info()
        self.results["ports"] = self.check_ports()
        self.results["processes"] = self.check_processes()
        self.results["logs"] = self.check_logs()
        self.results["dependencies"] = self.check_dependencies()
        self.results["configuration"] = self.check_configuration()
        self.results["backends"] = self.check_backend_connectivity()
        self.results["pid_files"] = self.check_pid_files()
        self.results["web_files"] = self.check_web_files()

        self.generate_summary()


# ============================================================
# Main Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic tool for Everything About Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/diagnose.py              # Run full diagnosis
  python scripts/diagnose.py --save       # Run and save report
  python scripts/diagnose.py --no-color   # Disable colors
        """,
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save report to JSON file",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path for report",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()

    # Disable colors if requested or if not in TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Find project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Run diagnostics
    try:
        diagnostic = DiagnosticReport(project_root)
        diagnostic.run_full_diagnosis()

        # Save report if requested
        if args.save:
            output_path = Path(args.output) if args.output else None
            diagnostic.save_report(output_path)

        # Exit with appropriate code
        error_count = len([e for e in diagnostic.reporter.errors if e.severity in ("ERROR", "CRITICAL")])
        sys.exit(1 if error_count > 0 else 0)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Diagnosis interrupted by user.{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Diagnostic tool crashed:{Colors.RESET}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
