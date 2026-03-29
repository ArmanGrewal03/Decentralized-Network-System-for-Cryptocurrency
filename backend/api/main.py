import json
from contextlib import asynccontextmanager

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from state import get_blockchain
from nodes import get_nodes, register_node as register_peer, sync_chain_from_peers

# Optional: start RabbitMQ consumer in background
def _start_background_consumers():
    try:
        from rabbitmq_consumer import start_consumer_background
        start_consumer_background()
    except Exception as e:
        print(f"RabbitMQ consumer not started: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _start_background_consumers()
    yield


app = FastAPI(title="COE892 Cryptocurrency API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class TransactionCreate(BaseModel):
    sender: str
    receiver: str
    amount: float


class MineRequest(BaseModel):
    miner_address: str


class NodeRegister(BaseModel):
    node_url: str


class DemoVerifyTransaction(BaseModel):
    transaction: dict


class DemoVerifyTransaction(BaseModel):
    transaction: dict


FRONTEND_PATH = Path(__file__).resolve().parent.parent.parent / "frontend"
INDEX_PATH = FRONTEND_PATH / "index.html"

@app.get("/")
async def root():
    if INDEX_PATH.exists():
        return RedirectResponse(url="/app")
    return {"service": "COE892 Decentralized Cryptocurrency", "docs": "/docs"}


@app.get("/chain")
async def get_chain():
    chain = get_blockchain()
    return {
        "chain": [b.to_dict() for b in chain.chain],
        "length": len(chain.chain),
    }


@app.get("/blocks/{index}")
async def get_block(index: int):
    chain = get_blockchain()
    if index < 0 or index >= len(chain.chain):
        raise HTTPException(status_code=404, detail="Block not found")
    return chain.chain[index].to_dict()


@app.get("/transactions/pending")
async def get_pending_transactions():
    chain = get_blockchain()
    return {"pending": chain.pending_transactions}


@app.post("/transactions")
async def create_transaction(tx: TransactionCreate):
    if tx.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    chain = get_blockchain()
    balance = chain.get_balance(tx.sender, include_pending=True)
    if balance < tx.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    try:
        created = chain.add_transaction(tx.sender, tx.receiver, tx.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        from rabbitmq_publisher import publish_transaction
        publish_transaction(created)
    except Exception:
        pass
    return {"message": "Transaction queued", "transaction": created}


@app.get("/balance/{address}")
async def get_balance(address: str):
    chain = get_blockchain()
    return {"address": address, "balance": chain.get_balance(address, include_pending=False)}


@app.post("/mine")
async def mine_block(req: MineRequest):
    chain = get_blockchain()
    block = chain.mine_block(req.miner_address)
    try:
        from rabbitmq_publisher import publish_block
        publish_block(block.to_dict())
    except Exception:
        pass
    return {"message": "Block mined", "block": block.to_dict()}


@app.get("/nodes")
async def list_nodes():
    return {"nodes": get_nodes()}


@app.post("/nodes/register")
async def register_node(node: NodeRegister):
    added = register_peer(node.node_url)
    return {"message": "Node registered" if added else "Node already registered", "url": node.node_url, "nodes": get_nodes()}


@app.post("/nodes/sync")
async def sync_nodes():
    result = sync_chain_from_peers()
    return result


@app.get("/health")
async def health():
    chain = get_blockchain()
    valid = chain.validate_chain()
    return {"status": "ok", "chain_valid": valid, "length": len(chain.chain)}

@app.get("/events")
async def get_system_events():
    from logger import get_events
    return {"events": get_events()}


@app.get("/demo/signed-sample")
async def get_signed_sample():
    import time
    import base64
    from wallet import sign_transaction, get_or_create_keypair
    priv, pub = get_or_create_keypair("_demo_forge")
    tx = {
        "id": "demo-sample", 
        "sender": "Alice", 
        "receiver": "Bob", 
        "amount": 1, 
        "timestamp": time.time(),
        "public_key": base64.b64encode(pub).decode()
    }
    # Create copy to sign
    sign_data = tx.copy()
    sig = sign_transaction(sign_data, priv)
    tx["signature"] = base64.b64encode(sig).decode()
    return {"tx": tx}

@app.post("/demo/verify-transaction")
async def demo_verify_transaction(body: DemoVerifyTransaction):
    try:
        from wallet import verify_transaction_signature
    except ImportError:
        raise HTTPException(status_code=501, detail="Cryptography not available")
    tx = body.transaction
    if not tx.get("signature") or not tx.get("public_key"):
        raise HTTPException(status_code=400, detail="Transaction must include signature and public_key for verification")
    if verify_transaction_signature(tx):
        return {"valid": True, "message": "Signature is valid"}
    raise HTTPException(status_code=400, detail="Invalid transaction signature")


@app.post("/demo/try-invalid-signature")
async def demo_try_invalid_signature():
    import time
    import base64
    try:
        from wallet import sign_transaction, verify_transaction_signature, get_or_create_keypair
    except ImportError:
        raise HTTPException(status_code=501, detail="Cryptography not available")
    # Build tx_a (amount 1), sign it. Build tx_b (amount 100) with same signature.
    priv, pub = get_or_create_keypair("_demo_forge")
    tx_a = {"id": "demo-forge", "sender": "attacker", "receiver": "bob", "amount": 1, "timestamp": time.time()}
    sig = sign_transaction(tx_a, priv)
    tx_b = {"id": "demo-forge", "sender": "attacker", "receiver": "bob", "amount": 100, "timestamp": tx_a["timestamp"]}
    tx_b["signature"] = base64.b64encode(sig).decode()
    tx_b["public_key"] = base64.b64encode(pub).decode()
    
    try:
        from logger import add_event
        add_event("Security", "Rejected forged transaction (attacker -> bob) with invalid signature", "error")
    except Exception:
        pass

    if verify_transaction_signature(tx_b):
        raise HTTPException(status_code=500, detail="Demo failed: expected verification to fail")
    raise HTTPException(status_code=400, detail="Invalid transaction signature")



@app.post("/demo/try-tampered-sync")
async def demo_try_tampered_sync():
    import time
    from state import get_blockchain
    chain = get_blockchain()
    
    # Simulate a fake "longer" chain from a malicious peer
    current_chain = [b.to_dict() for b in chain.chain]
    malicious_block = {
        "index": len(current_chain),
        "timestamp": time.time(),
        "transactions": [{"sender": "Hacker", "receiver": "Hacker", "amount": 99999, "is_coinbase": True}],
        "previous_hash": current_chain[-1]["hash"],
        "nonce": 1234, # Improper PoW
        "hash": "fake-hash"
    }
    malicious_chain = current_chain + [malicious_block]
    
    # This should trigger the replace_chain logic which runs validate_chain()
    if not chain.replace_chain(malicious_chain):
        raise HTTPException(status_code=400, detail="Untrusted Chain: Malicious peer rejected during sync.")
    return {"message": "Success (unexpected)"}

# Mount frontend at /static; serve app at /app
if FRONTEND_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH)), name="static")
    @app.get("/app")
    async def serve_app():
        return FileResponse(INDEX_PATH)
