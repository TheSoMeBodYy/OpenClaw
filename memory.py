import chromadb
from chromadb.utils import embedding_functions


class LongTermMemory:
    """
    Vector-based long-term memory using ChromaDB.
    Stores semantic chunks and retrieves relevant context for RAG.
    """

    def __init__(self):
        self.client = chromadb.Client()

        # SentenceTransformer embedding for semantic similarity
        self.embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name="openclaw_memory",
            embedding_function=self.embedding
        )

    def add_memory(self, text):
        """
        Add text entry to vector store.
        Hash used as deterministic ID.
        """
        self.collection.add(
            documents=[text],
            ids=[str(hash(text))]
        )

    def query(self, query, k=2):
        """
        Retrieve top-k relevant memories.
        """
        try:
            return self.collection.query(
                query_texts=[query],
                n_results=k
            )
        except:
            # Fail-safe fallback for query errors
            return {"documents": [[]]}