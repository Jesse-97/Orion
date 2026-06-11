from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("Loading BGE model... (this happens only once)")
            cls._instance.model = SentenceTransformer("BAAI/bge-base-en-v1.5")
        return cls._instance

    def embed_chunk(self, text: str):
        # Document chunks get embedded directly ie no prefixing
        return self.model.encode(text, normalize_embeddings=True)

    def embed_query(self, text: str):
        # User queries chunks get prefixed
        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        return self.model.encode(prefixed, normalize_embeddings=True)


embedding_model = EmbeddingModel()