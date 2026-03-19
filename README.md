# Decentralized Network System for Cryptocurrency

A lightweight blockchain-based cryptocurrency implementation leveraging **FastAPI**, **gRPC**, and **RabbitMQ**. This project implements a distributed ledger with peer-to-peer synchronization, proof-of-work mining, and cryptographically signed transactions.

## 🚀 Features

- **Distributed Ledger**: Immutable blockchain using SHA256 hashing and PoW.
- **P2P Sync**: High-performance node-to-node synchronization via gRPC.
- **Asynchronous Messaging**: Transaction broadcasting and block propagation powered by RabbitMQ.
- **Secure Transactions**: Ed25519 cryptographic signatures for all wallet transfers.
- **Modern Dashboard**: Real-time web interface for chain monitoring, mining, and transfers.
- **RESTful API**: Clean FastAPI interface for external integrations.

## 🛠️ Quick Start

### Local Installation

1. **Setup Environment**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Generate Native gRPC Code**:
   ```bash
   python generate_grpc.py
   ```

3. **Launch Server**:
   ```bash
   python run.py
   ```

The dashboard is accessible at `http://localhost:8000/app`.

### Docker Deployment

To spin up the full stack (including RabbitMQ) using Docker:

```bash
docker-compose up --build
```

## 🧪 Development

Tests are implemented using `pytest`:

```bash
cd backend
pytest tests/ -v
```

---
*Developed for research into decentralized networking and cryptographic ledger systems.*

