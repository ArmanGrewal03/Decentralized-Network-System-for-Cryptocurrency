import json
import threading
from pathlib import Path
from typing import Any

from logger import add_event

NODES_PATH = Path(__file__).resolve().parent / "data" / "nodes.json"
_nodes: list[str] | None = None


def _ensure_data_dir() -> None:
    NODES_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> list[str]:
    global _nodes
    if _nodes is not None:
        return _nodes
    _nodes = []
    if NODES_PATH.exists():
        try:
            with open(NODES_PATH) as f:
                data = json.load(f)
            _nodes = list(data.get("nodes", []))
        except Exception:
            pass
    return _nodes


def _save() -> None:
    _ensure_data_dir()
    with open(NODES_PATH, "w") as f:
        json.dump({"nodes": _load()}, f, indent=2)


def get_nodes() -> list[str]:
    return list(_load())


def register_node(node_url: str) -> bool:
    nodes = _load()
    node_url = (node_url or "").strip().rstrip("/")
    if not node_url:
        return False
    if node_url in nodes:
        return False
    nodes.append(node_url)
    global _nodes
    _nodes = nodes
    _save()
    return True


def sync_chain_from_peers() -> dict[str, Any]:
    import grpc
    from proto import blockchain_pb2 as pb2
    from proto import blockchain_pb2_grpc as pb2_grpc
    from state import get_blockchain

    chain = get_blockchain()
    current_len = len(chain.chain)
    errors = []

    for node_url in get_nodes():
        host_port = node_url.strip()
        if "://" in host_port:
            errors.append(f"Invalid gRPC address: {host_port}")
            add_event("gRPC", f"Sync skipped invalid peer address: {host_port}", "warning")
            continue

        try:
            add_event("gRPC", f"Sync request to peer {host_port}", "info")
            with grpc.insecure_channel(host_port) as channel:
                stub = pb2_grpc.BlockchainNodeStub(channel)
                resp = stub.GetChain(pb2.GetChainRequest(node_id="sync", from_index=0), timeout=5)
                add_event("gRPC", f"Sync response from {host_port}: {len(resp.blocks)} blocks", "info")
                
                blocks_data = []
                for b in resp.blocks:
                    blocks_data.append({
                        "index": b.index,
                        "timestamp": b.timestamp,
                        "previous_hash": b.previous_hash,
                        "nonce": b.nonce,
                        "hash": b.hash,
                        "transactions": json.loads(b.transactions_json or "[]"),
                    })
                
                if len(blocks_data) > current_len and chain.replace_chain(blocks_data):
                    add_event("gRPC", f"Sync adopted chain from {host_port} (height {len(chain.chain)})", "success")
                    return {
                        "replaced": True,
                        "from_node": host_port,
                        "new_length": len(chain.chain),
                        "errors": errors
                    }
        except Exception as e:
            errors.append(f"{host_port} sync error: {str(e)}")
            add_event("gRPC", f"Sync error from {host_port}: {str(e)}", "error")

    return {
        "replaced": False,
        "from_node": None,
        "new_length": len(chain.chain),
        "errors": errors
    }


def verify_local_grpc(round_trip_timeout: float = 2.0) -> None:
    import grpc
    from proto import blockchain_pb2 as pb2
    from proto import blockchain_pb2_grpc as pb2_grpc
    from config import GRPC_HOST, GRPC_PORT, NODE_ID
    from state import get_blockchain

    target_host = GRPC_HOST
    if target_host in {"0.0.0.0", "::"}:
        target_host = "127.0.0.1"
    target = f"{target_host}:{GRPC_PORT}"

    try:
        add_event("gRPC", f"Verification ping to {target}", "info")
        with grpc.insecure_channel(target) as channel:
            stub = pb2_grpc.BlockchainNodeStub(channel)
            resp = stub.GetChain(
                pb2.GetChainRequest(node_id=f"{NODE_ID}-verify", from_index=0),
                timeout=round_trip_timeout,
            )
        local_len = len(get_blockchain().chain)
        if resp.length == local_len:
            add_event("gRPC", f"Verification OK: local={local_len}, grpc={resp.length}", "success")
        else:
            add_event("gRPC", f"Verification mismatch: local={local_len}, grpc={resp.length}", "warning")
    except Exception as e:
        add_event("gRPC", f"Verification error on {target}: {str(e)}", "error")


def verify_local_grpc_async() -> None:
    threading.Thread(target=verify_local_grpc, daemon=True).start()

