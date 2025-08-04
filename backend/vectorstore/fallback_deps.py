"""
Fallback Implementations for Optional Dependencies
================================================

This module provides fallback implementations when optional libraries
like sentence-transformers, torch, numpy, etc. are not available.
"""

import logging
from typing import List, Union, Any

logger = logging.getLogger(__name__)


class FallbackSentenceTransformer:
    """Fallback implementation when sentence-transformers is not available."""
    
    def __init__(self, model_name: str, **kwargs):
        """Initialize fallback transformer."""
        self.model_name = model_name
        logger.warning(
            f"SentenceTransformer '{model_name}' not available. "
            "Install sentence-transformers for real embeddings."
        )
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> List[List[float]]:
        """Fallback encoding using simple hashing."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Simple hash-based embeddings (not semantically meaningful)
        embeddings = []
        for text in texts:
            # Create deterministic "embedding" from text hash
            text_hash = hash(text)
            embedding = [float((text_hash + i) % 1000) / 1000.0 for i in range(384)]
            embeddings.append(embedding)
        
        return embeddings


class FallbackTorch:
    """Fallback implementation when torch is not available."""
    
    class cuda:
        @staticmethod
        def is_available():
            return False
        
        @staticmethod
        def get_device_name():
            return "cpu"
        
        @staticmethod
        def empty_cache():
            pass
    
    class backends:
        class mps:
            @staticmethod
            def is_available():
                return False


class FallbackNumpy:
    """Fallback numpy-like operations."""
    
    @staticmethod
    def array(data):
        """Convert to list (fallback for np.array)."""
        return data if isinstance(data, list) else [data]
    
    @staticmethod
    def shape(arr):
        """Get shape of list-based array."""
        if not isinstance(arr, list):
            return ()
        if not arr:
            return (0,)
        if isinstance(arr[0], list):
            return (len(arr), len(arr[0]) if arr else 0)
        return (len(arr),)


# Export fallback classes
__all__ = ['FallbackSentenceTransformer', 'FallbackTorch', 'FallbackNumpy']
