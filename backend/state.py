from blockchain.chain import Blockchain
from config import CHAIN_PATH

_blockchain: Blockchain | None = None


def get_blockchain() -> Blockchain:
    global _blockchain
    if _blockchain is None:
        _blockchain = Blockchain(persist_path=CHAIN_PATH)
    return _blockchain
