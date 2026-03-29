import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .block import Block
from .transaction import create_transaction

try:
    from wallet import sign_tx_if_wallet, verify_transaction_signature
    from logger import add_event
except ImportError:
    sign_tx_if_wallet = lambda tx: tx
    verify_transaction_signature = lambda tx: True
    def add_event(cat, msg, lvl="info"): print(f"[{cat}] {msg}")

DIFFICULTY = 4
LEADING_ZEROS = "0" * DIFFICULTY
GENESIS_RECEIVER = "system"
REWARD_AMOUNT = 10.0



class Blockchain:

    def __init__(self, persist_path: str | Path | None = None):
        self.chain: list[Block] = []
        self.pending_transactions: list[dict[str, Any]] = []
        self.persist_path = Path(persist_path) if persist_path else None
        self._load_or_create_genesis()

    def _load_or_create_genesis(self) -> None:
        if self.persist_path and self.persist_path.exists():
            self._load_from_file()
            return
        # Genesis block
        genesis_tx = create_transaction("system", GENESIS_RECEIVER, 0)
        genesis_tx["is_coinbase"] = True
        genesis = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0",
        )
        genesis.nonce = self._proof_of_work(genesis)
        genesis.hash = genesis.compute_hash()
        self.chain.append(genesis)
        add_event("Consensus", "Genesis block created.", "success")
        self._save()

    def _proof_of_work(self, block: Block) -> int:
        nonce = 0
        while True:
            block.nonce = nonce
            h = block.compute_hash()
            if h.startswith(LEADING_ZEROS):
                return nonce
            nonce += 1

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, sender: str, receiver: str, amount: float, tx_id: str | None = None) -> dict[str, Any]:
        tx = create_transaction(sender, receiver, amount, tx_id)
        if not verify_transaction_signature(tx):
            add_event("Security", f"Rejected transaction from {sender}: Invalid signature.", "error")
            raise ValueError("Invalid transaction signature")
        tx = sign_tx_if_wallet(tx)
        self.pending_transactions.append(tx)
        add_event("Network", f"Transaction added to pool: {sender} -> {receiver} ({amount} COIN)", "info")
        return tx

    def mine_block(self, miner_address: str) -> Block | None:
        # Allow mining even with no pending transactions (block contains only coinbase reward)
        # Coinbase reward
        reward = create_transaction("system", miner_address, REWARD_AMOUNT)
        reward["is_coinbase"] = True
        block_txs = [reward] + self.pending_transactions.copy()
        self.pending_transactions.clear()

        last = self.get_last_block()
        new_block = Block(
            index=last.index + 1,
            timestamp=time.time(),
            transactions=block_txs,
            previous_hash=last.hash,
        )
        new_block.nonce = self._proof_of_work(new_block)
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        add_event("Mining", f"Mined Block #{new_block.index} successfully (Nonce: {new_block.nonce})", "success")
        self._save()
        return new_block

    def get_balance(self, address: str, include_pending: bool = False) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("is_coinbase"):
                    if tx["receiver"] == address:
                        balance += tx["amount"]
                else:
                    if tx["sender"] == address:
                        balance -= tx["amount"]
                    if tx["receiver"] == address:
                        balance += tx["amount"]
        if include_pending:
            for tx in self.pending_transactions:
                if tx["sender"] == address:
                    balance -= tx["amount"]
                if tx["receiver"] == address:
                    balance += tx["amount"]
        return balance

    def validate_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.previous_hash != prev.hash:
                return False
            if not curr.hash.startswith(LEADING_ZEROS):
                return False
            recomputed = curr.compute_hash()
            if curr.hash != recomputed:
                return False
            for tx in curr.transactions:
                if tx.get("signature") and not verify_transaction_signature(tx):
                    return False
        return True

    def replace_chain(self, new_chain_data: list[dict[str, Any]]) -> bool:
        new_blocks = [Block.from_dict(b) for b in new_chain_data]
        if len(new_blocks) <= len(self.chain):
            add_event("Consensus", f"Rejected chain from peer: Shorter or equal length ({len(new_blocks)}).", "warning")
            return False
            
        temp_blockchain = Blockchain()
        temp_blockchain.chain = new_blocks
        if not temp_blockchain.validate_chain():
            add_event("Security", "REJECTED peer node: Chain validation failed (Tampered/Corrupt).", "error")
            return False

        self.chain = new_blocks
        add_event("Consensus", f"Adopted longer valid chain from peer (New Height: {len(self.chain)}).", "success")
        self._save()
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": [b.to_dict() for b in self.chain],
            "pending_transactions": self.pending_transactions,
            "length": len(self.chain),
        }

    def _save(self) -> None:
        if not self.persist_path:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persist_path, "w") as f:
            json.dump(
                {"chain": [b.to_dict() for b in self.chain], "pending": self.pending_transactions},
                f,
                indent=2,
            )

    def _load_from_file(self) -> None:
        with open(self.persist_path) as f:
            data = json.load(f)
        self.chain = [Block.from_dict(b) for b in data["chain"]]
        self.pending_transactions = data.get("pending", [])
