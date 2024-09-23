import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import chromadb
import tempfile
import shutil

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import os

class OmniLogVectorStore:
    def __init__(self, path: Optional[str] = None):
        if path is None:
            # Use ~/.webwright/chromadb as the default path
            home_dir = os.path.expanduser('~')
            default_path = os.path.join(home_dir, '.webwright', 'chromadb')
            os.makedirs(default_path, exist_ok=True)
            self.path = default_path
        else:
            self.path = path
        
        self.client = chromadb.PersistentClient(
            path=self.path,
            settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection("omnilog")
        
    def add_entry(self, entry: Dict[str, Any]) -> str:
        entry_id = entry.get('id') or entry['timestamp']
        
        if entry['type'] == 'llm_response' and isinstance(entry['content'], list):
            # Handle structured content for LLM responses with tool calls
            content = json.dumps(entry['content'])
        elif entry['type'] == 'tool_call' and isinstance(entry['content'], list):
            # Handle structured content for tool results
            content = json.dumps(entry['content'])
        else:
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
        entries = []
        for metadata in results['metadatas']:
            try:
                entry = json.loads(metadata['full_entry'])
                if entry['type'] in ['llm_response', 'tool_call'] and isinstance(entry['content'], str):
                    try:
                        # Attempt to parse the content as JSON
                        entry['content'] = json.loads(entry['content'])
                    except json.JSONDecodeError:
                        # If parsing fails, keep the content as is
                        pass
                entries.append(entry)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse entry: {metadata['full_entry']}")
                continue

        # Sort the entries by timestamp in descending order
        sorted_entries = sorted(entries, key=lambda x: x['timestamp'], reverse=True)

        # Return the first 'limit' entries in chronological order
        return list(reversed(sorted_entries[:limit]))

    def search_entries_with_context(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], Optional[Dict[str, Any]]]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["metadatas", "documents", "distances"]
        )
        
        logger.debug(f"Search query: {query}")
        logger.debug(f"Number of search results: {len(results['metadatas'][0])}")
        
        all_entries = self._get_all_sorted_entries()
        entries_with_context = []
        
        for i, metadata in enumerate(results['metadatas'][0]):
            current_entry = json.loads(metadata['full_entry'])
            adjacent_entry = self._get_adjacent_entry(current_entry, all_entries)
            
            entries_with_context.append((current_entry, adjacent_entry))
            
            logger.debug(f"Current entry: {current_entry['type']} - {current_entry['content'][:50]}...")
            logger.debug(f"Adjacent entry: {adjacent_entry['type'] if adjacent_entry else None} - {adjacent_entry['content'][:50] if adjacent_entry else None}...")
            logger.debug(f"Distance: {results['distances'][0][i]}")
        
        return entries_with_context

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

    def build_omnilog_with_context(self, recent_count: int = 10, query: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        logger.debug(f"Building OmniLog with context. Recent count: {recent_count}, Query: {query}, Top k: {top_k}")

        # Get recent entries
        recent_entries = self.get_recent_entries(recent_count)
        logger.debug(f"Retrieved {len(recent_entries)} recent entries")

        if query:
            search_results = self.search_entries(query, top_k)
            logger.debug(f"Retrieved {len(search_results)} search results for query: {query}")
        else:
            search_results = []

        # Combine recent entries and search results, removing duplicates
        all_entries = []
        seen_contents = set()

        def add_entry_if_unique(entry):
            content = entry['content']
            if content not in seen_contents:
                all_entries.append(entry)
                seen_contents.add(content)
                logger.debug(f"Added unique entry: {entry['type']} - {content[:50]}...")
            else:
                logger.debug(f"Skipped duplicate entry: {entry['type']} - {content[:50]}...")

        # Add recent entries first
        for entry in recent_entries:
            add_entry_if_unique(entry)

        # Add search results
        for entry in search_results:
            add_entry_if_unique(entry)

        # Sort all entries by timestamp
        all_entries.sort(key=lambda x: x['timestamp'])
        logger.debug(f"Sorted {len(all_entries)} unique entries")

        # Build context with proper alternation
        context = []
        for i, entry in enumerate(all_entries):
            if entry['type'] == 'user':
                context.append(entry)
                logger.debug(f"Added user entry to context: {entry['content'][:50]}...")
                # If next entry is assistant, add it
                if i + 1 < len(all_entries) and all_entries[i + 1]['type'] == 'assistant':
                    context.append(all_entries[i + 1])
                    logger.debug(f"Added following assistant entry to context: {all_entries[i + 1]['content'][:50]}...")
            elif entry['type'] == 'assistant' and (not context or context[-1]['type'] == 'user'):
                # Add assistant message if it's the first message or follows a user message
                context.append(entry)
                logger.debug(f"Added assistant entry to context: {entry['content'][:50]}...")

        # Ensure the context starts with a user message if possible
        if context and context[0]['type'] == 'assistant':
            removed_entry = context.pop(0)
            logger.debug(f"Removed initial assistant entry: {removed_entry['content'][:50]}...")

        # Add the new query at the end if it's not already there
        if query and (not context or context[-1]['content'] != query):
            new_entry = {'type': 'user', 'content': query, 'timestamp': datetime.now().isoformat()}
            context.append(new_entry)
            logger.debug(f"Added new query to context: {new_entry['content'][:50]}...")

        logger.debug(f"Final context has {len(context)} entries")
        return context

    def _get_all_sorted_entries(self) -> List[Dict[str, Any]]:
        results = self.collection.get()
        entries = [json.loads(metadata['full_entry']) for metadata in results['metadatas']]
        return sorted(entries, key=lambda x: x['timestamp'])

    def _get_adjacent_entry(self, entry: Dict[str, Any], all_entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        current_index = next((i for i, e in enumerate(all_entries) if e['timestamp'] == entry['timestamp']), None)
        
        if current_index is not None:
            if entry['type'] == 'assistant':
                # Get the immediately previous user input
                for i in range(current_index - 1, -1, -1):
                    if all_entries[i]['type'] == 'user':
                        return all_entries[i]
            elif entry['type'] == 'user':
                # Get the immediately next assistant response
                for i in range(current_index + 1, len(all_entries)):
                    if all_entries[i]['type'] == 'assistant':
                        return all_entries[i]
        
        return None
    
    def _serialize_content(self, content: Any) -> str:
        if isinstance(content, dict):
            return json.dumps(content)
        elif isinstance(content, str):
            return content
        else:
            return str(content)