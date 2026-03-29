import time
from typing import Any

# In-memory event storage for demo purposes
_events: list[dict[str, Any]] = []

def add_event(type: str, message: str, level: str = "info") -> None:
    """ Adds a system event for the frontend console. """
    event = {
        "timestamp": time.time(),
        "type": type.capitalize(), # Consensus, Network, Security, Mining
        "message": message,
        "level": level # info, success, warning, error
    }
    global _events
    _events.append(event)
    # Keep last 50 events
    if len(_events) > 50:
        _events.pop(0)
    print(f"[{type.upper()}] {message}")

def get_events() -> list[dict[str, Any]]:
    """ Returns the list of system events. """
    return _events
