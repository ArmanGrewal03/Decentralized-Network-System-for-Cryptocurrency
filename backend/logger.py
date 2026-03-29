import time
from typing import Any
from pathlib import Path

_events: list[dict[str, Any]] = []
_LOG_PATH = Path(__file__).resolve().parent / "data" / "network.log"


def _ensure_log_file() -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LOG_PATH.touch(exist_ok=True)

def add_event(type: str, message: str, level: str = "info") -> None:
    event = {
        "timestamp": time.time(),
        "type": type.capitalize(),
        "message": message,
        "level": level
    }
    global _events
    _events.append(event)
    if len(_events) > 50:
        _events.pop(0)
    
    if type.lower() in ["rabbitmq", "grpc"]:
        log_to_file(f"[{type.upper()}] {message}")

def log_to_file(message: str) -> None:
    _ensure_log_file()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(_LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def get_events() -> list[dict[str, Any]]:
    return _events


_ensure_log_file()
