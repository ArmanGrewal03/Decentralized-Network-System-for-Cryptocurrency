# Decentralized Network System for Cryptocurrency

A lightweight blockchain-based cryptocurrency implementation leveraging FastAPI, gRPC, and RabbitMQ. This project implements a distributed ledger with peer-to-peer synchronization, proof-of-work mining, and cryptographically signed transactions.

## Features

- **Distributed Ledger**: Immutable blockchain using SHA256 hashing and PoW.
- **P2P Sync**: High-performance node-to-node synchronization via gRPC.
- **Asynchronous Messaging**: Transaction broadcasting and block propagation powered by RabbitMQ.
- **Secure Transactions**: Ed25519 cryptographic signatures for all wallet transfers.
- **Modern Dashboard**: Real-time web interface for chain monitoring, mining, and transfers.
- **RESTful API**: Clean FastAPI interface for external integrations.

## Quick Start

The dashboard is accessible at `http://localhost:8000/app`.

### Docker Deployment

To spin up the full stack (including RabbitMQ) using Docker:

```bash
docker-compose up --build
```

### Network Logs
All infrastructure activity (RabbitMQ and gRPC) is logged to `backend/data/network.log`. You can monitor this in real-time using `tail`:

```bash
tail -f backend/data/network.log
```

## Development

Tests are implemented using `pytest`:

```bash
cd backend
pytest tests/ -v
```

---
