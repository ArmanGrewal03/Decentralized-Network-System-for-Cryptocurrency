import sys
import threading
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))


def run_grpc():
    from grpc_server import serve
    serve()


def run_api():
    import uvicorn
    from config import API_HOST, API_PORT
    uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, reload=False)


if __name__ == "__main__":
    grpc_thread = threading.Thread(target=run_grpc, daemon=True)
    grpc_thread.start()
    run_api()
