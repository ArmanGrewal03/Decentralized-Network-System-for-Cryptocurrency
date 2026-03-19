import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
PROTO_FILE = BACKEND / "proto" / "blockchain.proto"
OUT = BACKEND

def main():
    if not PROTO_FILE.exists():
        print(f"Proto not found: {PROTO_FILE}")
        sys.exit(1)
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        "-I.", "--python_out=.", "--grpc_python_out=.",
        "proto/blockchain.proto",
    ]
    subprocess.run(cmd, cwd=BACKEND, check=True)
    print("Generated proto/blockchain_pb2.py and proto/blockchain_pb2_grpc.py")

if __name__ == "__main__":
    main()
