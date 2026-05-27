import os
import json
import logging
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from google import genai

class LocalRAGEngine:
    """
    [Local RAG V3]
    - Privacy-First: Pre-masks content before embedding.
    - Lightweight: Uses NumPy for vector search to avoid heavy DB dependencies.
    - Incremental: Tracks file modification times to update only changed files.
    """
    
    def __init__(self, parent_cli: Any, index_path: str = ".antigravity/rag_index.json"):
        self.parent = parent_cli
        self.index_path = index_path
        self.logger = logging.getLogger("RAG")
        self._standalone_client = None
        
        # In-memory storage
        self.index_data: Dict[str, Any] = {
            "version": "V3",
            "last_scan": "",
            "files": {}, # path -> {mtime, hash, chunks: [{text, embedding}]}
        }
        
        self.load_index()

    def _get_client(self):
        """Retrieves or creates a GenAI client for embeddings."""
        # 1. Try backend client
        client = getattr(self.parent.backend, 'client', None)
        if client and hasattr(client, 'aio'):
            return client
        
        # 2. Try standalone client if API key is available
        if not self._standalone_client:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self._standalone_client = genai.Client(api_key=api_key)
        
        return self._standalone_client

    def load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.index_data = json.load(f)
                self.logger.info(f"Loaded RAG index with {len(self.index_data['files'])} files.")
            except Exception as e:
                self.logger.error(f"Failed to load RAG index: {e}")

    def save_index(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save RAG index: {e}")

    async def scan_and_index(self, root_dir: str = "."):
        """Scans workspace and updates the index incrementally."""
        self.logger.info(f"Starting incremental scan of {root_dir}...")
        
        for root, dirs, files in os.walk(root_dir):
            # Respect exclude_paths from CLI config
            dirs[:] = [d for d in dirs if not self.parent.is_path_ignored(os.path.join(root, d))]
            
            for file in files:
                path = os.path.join(root, file)
                if self.parent.is_path_ignored(path):
                    continue
                
                # Simple text file check (skip binaries)
                if not any(file.endswith(ext) for ext in ['.txt', '.md', '.py', '.js', '.ts', '.yaml', '.json', '.c', '.cpp', '.h', '.go', '.java']):
                    continue

                # Check for updates
                try:
                    mtime = os.path.getmtime(path)
                except: continue
                
                file_info = self.index_data["files"].get(path, {})
                
                if file_info.get("mtime") == mtime:
                    continue
                
                self.logger.info(f"Indexing/Updating file: {path}")
                await self._index_file(path, mtime)
        
        self.index_data["last_scan"] = datetime.now().isoformat()
        self.save_index()

    async def _index_file(self, path: str, mtime: float):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return

            # [Privacy-First] Mask content BEFORE embedding
            masked_content = self.parent.protector.mask(content)
            
            # Chunking (Simple paragraph-based for CLI)
            chunks = [c.strip() for c in masked_content.split('\n\n') if len(c.strip()) > 20]
            if not chunks: # Fallback if no double newlines
                chunks = [masked_content[i:i+1000] for i in range(0, len(masked_content), 1000)]
            
            indexed_chunks = []
            for chunk in chunks:
                embedding = await self._get_embedding(chunk)
                if embedding:
                    indexed_chunks.append({
                        "text": chunk,
                        "embedding": embedding
                    })
            
            if indexed_chunks:
                self.index_data["files"][path] = {
                    "mtime": mtime,
                    "chunks": indexed_chunks
                }
        except Exception as e:
            self.logger.error(f"Error indexing {path}: {e}")

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates embedding via Gemini API."""
        try:
            client = self._get_client()
            if client:
                # Use standard embedding model
                result = await client.aio.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                return result.embeddings[0].values
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
        return None

    async def search(self, query: str, top_k: int = 3) -> str:
        """Performs vector search across the index."""
        # [Privacy-First] Mask query before searching to match masked index
        masked_query = self.parent.protector.mask(query)
        query_embedding = await self._get_embedding(masked_query)
        if not query_embedding:
            return ""

        query_vec = np.array(query_embedding)
        all_results = []

        for path, file_info in self.index_data["files"].items():
            for chunk in file_info["chunks"]:
                try:
                    chunk_vec = np.array(chunk["embedding"])
                    
                    # Prevent zero-division
                    norm_q = np.linalg.norm(query_vec)
                    norm_c = np.linalg.norm(chunk_vec)
                    if norm_q == 0 or norm_c == 0: continue

                    # Cosine Similarity
                    similarity = np.dot(query_vec, chunk_vec) / (norm_q * norm_c)
                    all_results.append({
                        "path": path,
                        "text": chunk["text"],
                        "score": float(similarity)
                    })
                except: continue

        # Sort by score descending
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = all_results[:top_k]

        if not top_results:
            return ""

        context = "\n--- [Local RAG Context] ---\n"
        for res in top_results:
            # Only include results with reasonable confidence
            if res['score'] > 0.4:
                context += f"Source: {res['path']} (Score: {res['score']:.2f})\nContent: {res['text']}\n\n"
        
        return context if len(context) > 30 else ""
