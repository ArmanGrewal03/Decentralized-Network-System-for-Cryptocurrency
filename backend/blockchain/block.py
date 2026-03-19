import hashlib
import json
import time
from typing import Any


class Block:

    def __init__(
        self,
        index: int,
        timestamp: float,
        transactions: list[dict[str, Any]],
        previous_hash: str,
        nonce: int = 0,
    ):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_data = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_data.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        b = cls(
            index=data["index"],
            timestamp=data["timestamp"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
        )
        b.hash = data.get("hash", b.hash)
        return b

    def __repr__(self) -> str:
        return f"Block(index={self.index}, hash={self.hash[:16]}...)"
