from rag_service.app.server import serve
from shared.config import setup_logging

def main():
    setup_logging()
    serve()