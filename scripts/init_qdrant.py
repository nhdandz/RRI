"""Initialize Qdrant vector database collections."""

from src.storage.vector.qdrant_client import VectorStore


def main():
    store = VectorStore()
    store.init_collections()
    print("Qdrant collections initialized successfully!")


if __name__ == "__main__":
    main()
