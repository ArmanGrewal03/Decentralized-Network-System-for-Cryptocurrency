import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root_redirect_or_json():
    r = client.get("/")
    assert r.status_code in (200, 307)


def test_chain():
    r = client.get("/chain")
    assert r.status_code == 200
    data = r.json()
    assert "chain" in data
    assert "length" in data
    assert data["length"] >= 1


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "chain_valid" in data
    assert "length" in data


def test_balance():
    r = client.get("/balance/alice")
    assert r.status_code == 200
    data = r.json()
    assert data["address"] == "alice"
    assert "balance" in data


def test_mine():
    r = client.post("/mine", json={"miner_address": "miner1"})
    assert r.status_code == 200
    data = r.json()
    assert "block" in data
    assert data["block"]["index"] >= 0


def test_transactions_flow():
    # Mine to get balance
    client.post("/mine", json={"miner_address": "alice"})
    r = client.get("/balance/alice")
    assert r.json()["balance"] == 10.0
    # Send
    r = client.post("/transactions", json={"sender": "alice", "receiver": "bob", "amount": 2.0})
    assert r.status_code == 200
    assert "transaction" in r.json()
    # Mine to confirm
    client.post("/mine", json={"miner_address": "miner"})
    r = client.get("/balance/alice")
    assert r.json()["balance"] == 8.0
    r = client.get("/balance/bob")
    assert r.json()["balance"] == 2.0


def test_nodes_list():
    r = client.get("/nodes")
    assert r.status_code == 200
    assert "nodes" in r.json()


def test_nodes_register():
    r = client.post("/nodes/register", json={"node_url": "peer1:50051"})
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "peer1:50051" in data["nodes"]


def test_nodes_sync():
    r = client.post("/nodes/sync")
    assert r.status_code == 200
    data = r.json()
    assert "replaced" in data
    assert "new_length" in data
