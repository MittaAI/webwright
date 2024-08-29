import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from vector_store import VectorStore

class OmniLogVectorStore(VectorStore):
    def __init__(self, storage_path: str = 'omnilog_vector_store.json'):
        super().__init__(storage_path)

    def add_entry(self, entry: Dict[str, Any]) -> str:
        """Add a single OmniLog entry to the vector store."""
        entry_id = entry.get('id') or str(datetime.now().timestamp())
        content = self._serialize_content(entry['content'])
        
        node = {
            'id': entry_id,
            'text': content,
            'timestamp': entry.get('timestamp') or datetime.now().isoformat(),
            'type': entry.get('type', 'default'),
            'metadata': entry
        }
        
        self.add([node])
        return entry_id

    def get_recent_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent entries from the vector store."""
        sorted_entries = sorted(
            self.node_dict.values(),
            key=lambda x: x['timestamp'],
            reverse=True
        )
        return [entry['metadata'] for entry in sorted_entries[:limit]]

    def search_entries(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search entries using vector similarity."""
        query_embedding = self.vectorize(query)
        similar_ids = self.query(query_embedding, top_k)
        return [self.node_dict[id]['metadata'] for id in similar_ids]

    def search_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Search entries within a specific date range."""
        return [
            entry['metadata'] for entry in self.node_dict.values()
            if start_date <= datetime.fromisoformat(entry['timestamp']) <= end_date
        ]

    def search_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        """Search entries by type."""
        return [
            entry['metadata'] for entry in self.node_dict.values()
            if entry['type'] == entry_type
        ]

    def _serialize_content(self, content: Any) -> str:
        """Serialize the content for vectorization."""
        if isinstance(content, dict):
            return json.dumps(content)
        return str(content)

    def build_omnilog(self, recent_count: int = 10, query: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Build OmniLog instance with recent entries and optionally similar entries."""
        recent_entries = self.get_recent_entries(recent_count)
        
        if query:
            similar_entries = self.search_entries(query, top_k)
            # Combine recent and similar entries, removing duplicates
            combined_entries = recent_entries + [entry for entry in similar_entries if entry not in recent_entries]
            return combined_entries[:max(recent_count, top_k)]
        
        return recent_entries