import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import chromadb
import tempfile
import shutil

class OmniLogVectorStore:
    def __init__(self, path: Optional[str] = None):
        if path is None:
            self.temp_dir = tempfile.mkdtemp()
            path = self.temp_dir
        else:
            self.temp_dir = None
        
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("omnilog")

    def add_entry(self, entry: Dict[str, Any]) -> str:
        entry_id = entry.get('id') or str(datetime.now().timestamp())
        content = self._serialize_content(entry['content'])
        
        self.collection.add(
            documents=[content],
            metadatas=[{
                'timestamp': entry['timestamp'],
                'type': entry['type'],
                'full_entry': json.dumps(entry)
            }],
            ids=[entry_id]
        )
        
        return entry_id

    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        result = self.collection.get(ids=[entry_id])
        if result['metadatas']:
            return json.loads(result['metadatas'][0]['full_entry'])
        return None

    def get_recent_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        results = self.collection.get()
        entries = [json.loads(metadata['full_entry']) for metadata in results['metadatas']]
        sorted_entries = sorted(entries, key=lambda x: x['timestamp'], reverse=True)
        return sorted_entries[:limit]

    def search_entries(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return [json.loads(metadata['full_entry']) for metadata in results['metadatas'][0]]

    def search_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        results = self.collection.get()
        entries = [json.loads(metadata['full_entry']) for metadata in results['metadatas']]
        filtered_entries = [
            entry for entry in entries
            if start_date.isoformat() <= entry['timestamp'] <= end_date.isoformat()
        ]
        return filtered_entries

    def search_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        results = self.collection.get(
            where={"type": entry_type}
        )
        return [json.loads(metadata['full_entry']) for metadata in results['metadatas']]

    def build_omnilog(self, recent_count: int = 10, query: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        recent_entries = self.get_recent_entries(recent_count)
        
        if query:
            similar_entries = self.search_entries(query, top_k)
            combined_entries = recent_entries + [entry for entry in similar_entries if entry not in recent_entries]
            return combined_entries[:max(recent_count, top_k)]
        
        return recent_entries

    def _serialize_content(self, content: Any) -> str:
        if isinstance(content, dict):
            return json.dumps(content)
        return str(content)

    def __del__(self):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)