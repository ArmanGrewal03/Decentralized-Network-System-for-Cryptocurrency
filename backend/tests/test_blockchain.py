import pytest

from blockchain.block import Block
from blockchain.chain import Blockchain
from state import get_blockchain


def test_block_compute_hash():
    block = Block(0, 1.0, [], "0", 0)
    h = block.compute_hash()
    assert isinstance(h, str)
    assert len(h) == 64


def test_block_to_dict_roundtrip():
    block = Block(1, 2.0, [{"a": 1}], "prev", 42)
    d = block.to_dict()
    block2 = Block.from_dict(d)
    assert block2.index == block.index
    assert block2.hash == block.hash


def test_chain_genesis():
    chain = get_blockchain()
    assert len(chain.chain) >= 1
    assert chain.chain[0].index == 0
    assert chain.chain[0].previous_hash == "0"


def test_add_transaction_and_mine():
    chain = get_blockchain()
    initial_len = len(chain.chain)
    chain.add_transaction("alice", "bob", 5.0)
    assert len(chain.pending_transactions) == 1
    block = chain.mine_block("miner")
    assert block is not None
    assert len(chain.chain) == initial_len + 1
    assert len(chain.pending_transactions) == 0
    assert block.index == initial_len


def test_balance_after_mine():
    chain = get_blockchain()
    chain.mine_block("alice")
    assert chain.get_balance("alice", include_pending=False) == 10.0


def test_balance_after_send_and_mine():
    chain = get_blockchain()
    chain.mine_block("alice")
    chain.add_transaction("alice", "bob", 3.0)
    chain.mine_block("miner")
    assert chain.get_balance("alice", include_pending=False) == 7.0
    assert chain.get_balance("bob", include_pending=False) == 3.0


def test_validate_chain():
    chain = get_blockchain()
    assert chain.validate_chain() is True


def test_replace_chain_longer_valid():
    chain = get_blockchain()
    chain.mine_block("a")
    chain.mine_block("b")
    longer = [b.to_dict() for b in chain.chain]
    chain.chain = [chain.chain[0]]  # shorten
    replaced = chain.replace_chain(longer)
    assert replaced is True
    assert len(chain.chain) == len(longer)


def test_replace_chain_shorter_rejected():
    chain = get_blockchain()
    chain.mine_block("a")
    shorter = [chain.chain[0].to_dict()]
    orig_len = len(chain.chain)
    replaced = chain.replace_chain(shorter)
    assert replaced is False
    assert len(chain.chain) == orig_len
