"""
app/rag/document_loader.py
--------------------------
Handles loading, parsing, and chunking documents from data/documents/.
Supports TXT, MD, JSON, and CSV files, with graceful warning fallbacks for PDF.
"""

import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks with a specified size and overlap.
    Aims to split at paragraph or sentence boundaries where possible.
    """
    if not text:
        return []
        
    chunks = []
    # Split by paragraph first
    paragraphs = text.split("\n\n")
    
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If a single paragraph is larger than chunk_size, split it by characters
        if len(para) > chunk_size:
            # First, save any existing accumulated chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0
                
            start = 0
            while start < len(para):
                end = start + chunk_size
                chunks.append(para[start:end])
                start += chunk_size - chunk_overlap
            continue
            
        # Otherwise, accumulate
        new_length = len(para) if not current_chunk else current_length + len(para) + 2
        if new_length > chunk_size:
            # Chunk is full, save it
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = len(para)
        else:
            current_chunk.append(para)
            current_length = new_length
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks


class DocumentLoader:
    """Loader and parser for local document formats."""

    @staticmethod
    def load_file(file_path: str) -> str:
        """Load file contents as text depending on extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext in ['.txt', '.md', '.markdown']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
            elif ext == '.json':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    return json.dumps(data, indent=2)
                    
            elif ext == '.pdf':
                # Try to import pypdf for PDF support
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    text_parts = []
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    return "\n".join(text_parts)
                except ImportError:
                    logger.warning(
                        f"pypdf package is not installed. Skipping binary parsing of PDF: {file_path}. "
                        "Install pypdf to enable PDF ingestion."
                    )
                    return ""
            else:
                logger.warning(f"Unsupported file format: {ext} for file {file_path}")
                return ""
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return ""

    def load_and_chunk_directory(
        self, 
        directory_path: str, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Scan directory and parse all files into standard text chunk dictionaries.
        
        Returns:
            List of dicts: {text: str, metadata: dict}
        """
        parsed_chunks = []
        
        if not os.path.exists(directory_path):
            logger.warning(f"Directory path does not exist: {directory_path}")
            return parsed_chunks
            
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                content = self.load_file(file_path)
                if not content.strip():
                    continue
                    
                chunks = split_text(content, chunk_size, chunk_overlap)
                logger.info(f"Loaded {file} ({len(chunks)} chunks)")
                
                for idx, chunk in enumerate(chunks):
                    parsed_chunks.append({
                        "text": chunk,
                        "metadata": {
                            "source_file": file,
                            "file_path": file_path,
                            "chunk_index": idx,
                            "total_chunks": len(chunks)
                        }
                    })
                    
        return parsed_chunks
