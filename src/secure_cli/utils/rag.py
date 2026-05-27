import os
import json
import logging
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

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
        
        # In-memory storage
        self.index_data: Dict[str, Any] = {
            "version": "V3",
            "last_scan": "",
            "files": {}, # path -> {mtime, hash, chunks: [{text, embedding}]}
        }
        
        self.load_index()

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
                
                # Check for updates
                mtime = os.path.getmtime(path)
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
            
            indexed_chunks = []
            for chunk in chunks:
                embedding = await self._get_embedding(chunk)
                if embedding:
                    indexed_chunks.append({
                        "text": chunk,
                        "embedding": embedding
                    })
            
            self.index_data["files"][path] = {
                "mtime": mtime,
                "chunks": indexed_chunks
            }
        except Exception as e:
            self.logger.error(f"Error indexing {path}: {e}")

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates embedding via Gemini API."""
        try:
            # We use the client from the parent's backend
            if hasattr(self.parent.backend, 'client') and self.parent.backend.client:
                # Use standard embedding model
                result = await self.parent.backend.client.aio.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                return result.embeddings[0].values
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
        return None

    async def search(self, query: str, top_k: int = 3) -> str:
        """Performs vector search across the index."""
        query_embedding = await self._get_embedding(query)
        if not query_embedding:
            return ""

        query_vec = np.array(query_embedding)
        all_results = []

        for path, file_info in self.index_data["files"].items():
            for chunk in file_info["chunks"]:
                chunk_vec = np.array(chunk["embedding"])
                # Cosine Similarity
                similarity = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec))
                all_results.append({
                    "path": path,
                    "text": chunk["text"],
                    "score": float(similarity)
                })

        # Sort by score descending
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = all_results[:top_k]

        if not top_results:
            return ""

        context = "\n--- [Local RAG Context] ---\n"
        for res in top_results:
            context += f"Source: {res['path']} (Score: {res['score']:.2f})\nContent: {res['text']}\n\n"
        
        return context
