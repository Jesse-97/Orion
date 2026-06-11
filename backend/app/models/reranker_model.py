from sentence_transformers import CrossEncoder

class RerankerModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("Loading reranker model... (this happens only once)")
            cls._instance.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return cls._instance

    def score(self, query: str, passages: list[str]):
        pairs = [[query, passage] for passage in passages]
        return self.model.predict(pairs)


reranker_model = RerankerModel()