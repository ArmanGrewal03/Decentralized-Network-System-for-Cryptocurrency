import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from concurrent import futures
import grpc
from proto import blockchain_pb2 as pb2
from proto import blockchain_pb2_grpc as pb2_grpc
from state import get_blockchain
from config import GRPC_HOST, GRPC_PORT


class BlockchainNodeServicer(pb2_grpc.BlockchainNodeServicer):

    def GetChain(self, request, context):
        chain = get_blockchain()
        blocks = []
        for b in chain.chain:
            blocks.append(pb2.BlockMessage(
                index=b.index,
                timestamp=b.timestamp,
                previous_hash=b.previous_hash,
                nonce=b.nonce,
                hash=b.hash,
                transactions_json=json.dumps(b.transactions),
            ))
        return pb2.ChainResponse(blocks=blocks, length=len(blocks))

    def SubmitBlock(self, request, context):
        chain = get_blockchain()
        try:
            block_dict = {
                "index": request.index,
                "timestamp": request.timestamp,
                "previous_hash": request.previous_hash,
                "nonce": request.nonce,
                "hash": request.hash,
                "transactions": json.loads(request.transactions_json or "[]"),
            }
            from blockchain.block import Block
            block = Block.from_dict(block_dict)
            if len(chain.chain) == block.index:
                chain.chain.append(block)
                chain._save()
                return pb2.Ack(ok=True, message="Block accepted")
        except Exception as e:
            return pb2.Ack(ok=False, message=str(e))
        return pb2.Ack(ok=False, message="Block index mismatch")

    def StreamBlocks(self, request, context):
        chain = get_blockchain()
        start = request.after_index + 1
        for i in range(start, len(chain.chain)):
            b = chain.chain[i]
            yield pb2.BlockMessage(
                index=b.index,
                timestamp=b.timestamp,
                previous_hash=b.previous_hash,
                nonce=b.nonce,
                hash=b.hash,
                transactions_json=json.dumps(b.transactions),
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_BlockchainNodeServicer_to_server(BlockchainNodeServicer(), server)
    server.add_insecure_port(f"{GRPC_HOST}:{GRPC_PORT}")
    server.start()
    print(f"gRPC BlockchainNode server running on {GRPC_HOST}:{GRPC_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
