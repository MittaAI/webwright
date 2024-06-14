from typing import List, Any, Dict
import json
import os

from InstructorEmbedding import INSTRUCTOR

class EmbeddingGenerator:
    def __init__(self, model_name="hkunlp/instructor-xl"):
        self.model = INSTRUCTOR(model_name)

    def generate_embeddings(self, texts):
        embeddings = self.model.encode(texts).tolist()
        return embeddings

class VectorStore:
    """Simple custom Vector Store that uses local embeddings."""
    def __init__(self, storage_path: str = 'vector_store.json'):
        self.node_dict: Dict[str, Dict[str, Any]] = {}
        self.storage_path = storage_path
        self.embedding_generator = EmbeddingGenerator()
        self.load()

    def get(self, text_id: str) -> List[float]:
        """Get embedding by text ID."""
        return self.node_dict.get(text_id, {}).get('embedding', [])

    def add(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """Add nodes to index and vectorize them."""
        ids = []
        for node in nodes:
            text_id = node['id']
            text = node['text']
            embedding = self.vectorize(text)
            self.node_dict[text_id] = {
                'text': text,
                'embedding': embedding
            }
            ids.append(text_id)
        self.save()
        return ids

    def delete(self, text_id: str) -> None:
        """Delete node by text ID."""
        if text_id in self.node_dict:
            del self.node_dict[text_id]
        self.save()

    def query(self, query_embedding: List[float], top_k: int = 5) -> List[str]:
        """Get top-k nodes by similarity to the query embedding."""
        similarities = [
            (text_id, self.cosine_similarity(query_embedding, node['embedding']))
            for text_id, node in self.node_dict.items()
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [text_id for text_id, _ in similarities[:top_k]]

    def vectorize(self, text: str) -> List[float]:
        """Generate embeddings using the EmbeddingGenerator."""
        embedding = self.embedding_generator.generate_embeddings([text])[0]
        return embedding

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute the cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(a ** 2 for a in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def save(self) -> None:
        """Persist the vector store to a JSON file."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.node_dict, f, ensure_ascii=False, indent=4)

    def load(self) -> None:
        """Load the vector store from a JSON file."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                self.node_dict = json.load(f)