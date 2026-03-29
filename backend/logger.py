import time
from typing import Any
from pathlib import Path

_events: list[dict[str, Any]] = []

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
    log_path = Path(__file__).resolve().parent / "data" / "network.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def get_events() -> list[dict[str, Any]]:
    return _events
