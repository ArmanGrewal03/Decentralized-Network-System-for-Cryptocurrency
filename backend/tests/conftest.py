import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
def temp_data_paths(tmp_path, monkeypatch):
    """Point chain and wallet data to tmp_path so tests are isolated."""
    data = tmp_path / "data"
    data.mkdir()
    chain_path = data / "chain.json"
    nodes_path = data / "nodes.json"
    wallets_path = data / "wallets.json"

    import config
    monkeypatch.setattr(config, "CHAIN_PATH", chain_path)

    import state
    monkeypatch.setattr(state, "CHAIN_PATH", chain_path)
    state._blockchain = None

    import nodes
    monkeypatch.setattr(nodes, "NODES_PATH", nodes_path)
    monkeypatch.setattr(nodes, "_nodes", None)

    import wallet
    monkeypatch.setattr(wallet, "WALLETS_PATH", wallets_path)
    monkeypatch.setattr(wallet, "_wallets", None)

    yield tmp_path
