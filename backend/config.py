import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CHAIN_PATH = DATA_DIR / "chain.json"

# FastAPI
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# gRPC
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")

# RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

QUEUE_PENDING_TX = "pending_transactions"
QUEUE_NEW_BLOCKS = "new_blocks"
EXCHANGE_BLOCKS = "blockchain_blocks"

# Node identity (for multi-node)
NODE_ID = os.getenv("NODE_ID", "node1")
