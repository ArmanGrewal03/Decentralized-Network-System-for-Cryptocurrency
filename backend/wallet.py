import base64
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

WALLETS_PATH = Path(__file__).resolve().parent / "data" / "wallets.json"
_wallets: dict[str, dict[str, str]] | None = None


def _payload_for_signature(tx: dict[str, Any]) -> bytes:
    data = {
        "id": tx["id"],
        "sender": tx["sender"],
        "receiver": tx["receiver"],
        "amount": tx["amount"],
        "timestamp": tx["timestamp"],
    }
    return json.dumps(data, sort_keys=True).encode()


def _load_wallets() -> dict[str, dict[str, str]]:
    global _wallets
    if _wallets is not None:
        return _wallets
    _wallets = {}
    if WALLETS_PATH.exists():
        try:
            with open(WALLETS_PATH) as f:
                _wallets = json.load(f)
        except Exception:
            pass
    return _wallets


def _save_wallets() -> None:
    WALLETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WALLETS_PATH, "w") as f:
        json.dump(_load_wallets(), f, indent=2)


def _registered_public_key_bytes(address: str) -> bytes | None:
    if not address:
        return None
    wallet = _load_wallets().get(address)
    if not wallet:
        return None
    pub_b64 = wallet.get("public_key")
    if not pub_b64:
        return None
    try:
        return base64.b64decode(pub_b64)
    except Exception:
        return None


def get_or_create_keypair(address: str) -> tuple[bytes, bytes]:
    wallets = _load_wallets()
    if address in wallets:
        priv_b64 = wallets[address]["private_key"]
        pub_b64 = wallets[address]["public_key"]
        return base64.b64decode(priv_b64), base64.b64decode(pub_b64)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    wallets[address] = {
        "private_key": base64.b64encode(priv_bytes).decode(),
        "public_key": base64.b64encode(pub_bytes).decode(),
    }
    global _wallets
    _wallets = wallets
    _save_wallets()
    return priv_bytes, pub_bytes


def sign_transaction(tx: dict[str, Any], private_key_bytes: bytes) -> bytes:
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    payload = _payload_for_signature(tx)
    return private_key.sign(payload)


def verify_transaction_signature(tx: dict[str, Any]) -> bool:
    if not tx.get("signature") or not tx.get("public_key"):
        return True  # unsigned allowed for backward compat
    try:
        sender = (tx.get("sender") or "").strip()
        sig_b64 = tx["signature"]
        pub_b64 = tx["public_key"]
        if isinstance(sig_b64, str):
            signature = base64.b64decode(sig_b64)
        else:
            signature = sig_b64
        if isinstance(pub_b64, str):
            pub_bytes = base64.b64decode(pub_b64)
        else:
            pub_bytes = pub_b64
        if sender and sender != "system":
            registered_pub = _registered_public_key_bytes(sender)
            if registered_pub is not None and registered_pub != pub_bytes:
                return False
        public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        payload = _payload_for_signature(tx)
        public_key.verify(signature, payload)
        return True
    except Exception:
        return False


def sign_tx_if_wallet(tx: dict[str, Any]) -> dict[str, Any]:
    """Attempts to sign a transaction if the sender's wallet exists locally."""
    sender = tx.get("sender", "")
    if not sender or sender == "system":
        return tx
    
    try:
        priv_bytes, pub_bytes = get_or_create_keypair(sender)
        sig = sign_transaction(tx, priv_bytes)
        
        # Return a signed copy
        signed_tx = dict(tx)
        signed_tx["signature"] = base64.b64encode(sig).decode()
        signed_tx["public_key"] = base64.b64encode(pub_bytes).decode()
        return signed_tx
    except Exception as e:
        # If signing fails (e.g. key error), return original unsigned tx
        return tx
