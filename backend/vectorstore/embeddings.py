"""
Embedding Generator for AI Tech News Assistant
==============================================

This module handles text-to-vector conversion using Sentence Transformers.
It provides efficient embedding generation for article content to enable
semantic search and retrieval-augmented generation (RAG).
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, TYPE_CHECKING
from pathlib import Path

# Handle optional dependencies
try:
    from sentence_transformers import SentenceTransformer
    import torch
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    if not TYPE_CHECKING:
        # Create dummy classes for runtime
        class SentenceTransformer:
            pass
        class torch:
            class cuda:
                @staticmethod
                def is_available(): return False
                @staticmethod
                def get_device_name(): return ""
                @staticmethod
                def empty_cache(): pass
            class backends:
                class mps:
                    @staticmethod
                    def is_available(): return False
        class np:
            ndarray = list  # Fallback type

from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingGenerator:
    """
    High-performance embedding generator using Sentence Transformers.
    
    Features:
    - Multiple pre-trained model support
    - Batch processing for efficiency
    - GPU acceleration when available
    - Async-friendly interface
    - Caching and model management
    """
    
    # Default models ordered by performance/size trade-off
    DEFAULT_MODELS = [
        "all-MiniLM-L6-v2",      # Fast, good quality, 384 dimensions
        "all-mpnet-base-v2",     # Higher quality, 768 dimensions
        "multi-qa-MiniLM-L6-cos-v1",  # Optimized for Q&A
    ]
    
    def __init__(self, 
                 model_name: Optional[str] = None,
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Sentence transformer model name
            device: Device to use ('cpu', 'cuda', or None for auto)
            cache_dir: Directory to cache models
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required. Install with: "
                "pip install sentence-transformers"
            )
        
        self.model_name = model_name or self.DEFAULT_MODELS[0]
        self.device = device or self._detect_device()
        self.cache_dir = cache_dir or "./models"
        self.model: Optional[Any] = None  # SentenceTransformer when available
        self.embedding_dim: Optional[int] = None
        
        # Ensure cache directory exists
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Embedding generator initialized with model: {self.model_name}")
        logger.info(f"Using device: {self.device}")
    
    def _detect_device(self) -> str:
        """Detect the best available device."""
        if torch is None:
            return "cpu"
        
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"CUDA detected: {torch.cuda.get_device_name()}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon
            logger.info("Apple MPS detected")
        else:
            device = "cpu"
            logger.info("Using CPU")
        
        return device
    
    async def load_model(self) -> None:
        """
        Load the sentence transformer model asynchronously.
        
        Raises:
            RuntimeError: If model loading fails
        """
        if self.model is not None:
            logger.debug("Model already loaded")
            return
        
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                self._load_model_sync
            )
            
            # Get embedding dimension
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            error_msg = f"Failed to load model {self.model_name}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _load_model_sync(self) -> Any:  # Returns SentenceTransformer when available
        """Synchronous model loading."""
        return SentenceTransformer(
            self.model_name,
            device=self.device,
            cache_folder=self.cache_dir
        )
    
    async def generate_embeddings(self, 
                                texts: Union[str, List[str]],
                                batch_size: int = 32,
                                normalize: bool = True,
                                show_progress: bool = False) -> Any:  # Returns np.ndarray when available
        """
        Generate embeddings for input texts.
        
        Args:
            texts: Single text or list of texts to embed
            batch_size: Batch size for processing
            normalize: Whether to normalize embeddings
            show_progress: Show progress bar
            
        Returns:
            Numpy array of embeddings (shape: [n_texts, embedding_dim])
            
        Raises:
            ValueError: If texts is empty
            RuntimeError: If model is not loaded
        """
        # Ensure model is loaded
        if self.model is None:
            await self.load_model()
        
        # Handle single string input
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("No texts provided for embedding")
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            # Generate embeddings in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self._generate_embeddings_sync,
                texts,
                batch_size,
                normalize,
                show_progress
            )
            
            logger.info(f"Generated embeddings shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _generate_embeddings_sync(self, 
                                texts: List[str],
                                batch_size: int,
                                normalize: bool,
                                show_progress: bool) -> Any:  # Returns np.ndarray when available
        """Synchronous embedding generation."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
    
    async def embed_articles(self, 
                           articles: List[Dict[str, Any]],
                           content_field: str = "content",
                           title_field: str = "title",
                           combine_title_content: bool = True) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of articles.
        
        Args:
            articles: List of article dictionaries
            content_field: Field name containing article content
            title_field: Field name containing article title
            combine_title_content: Whether to combine title and content
            
        Returns:
            List of articles with embeddings added
            
        Raises:
            ValueError: If articles are invalid
        """
        if not articles:
            raise ValueError("No articles provided")
        
        # Extract texts for embedding
        texts = []
        valid_articles = []
        
        for article in articles:
            content = article.get(content_field, "").strip()
            title = article.get(title_field, "").strip()
            
            if not content:
                logger.warning(f"Skipping article with no content: {article.get('id', 'unknown')}")
                continue
            
            # Combine title and content if requested
            if combine_title_content and title:
                text = f"{title}\n\n{content}"
            else:
                text = content
            
            texts.append(text)
            valid_articles.append(article)
        
        if not texts:
            logger.warning("No valid articles with content found")
            return []
        
        # Generate embeddings
        logger.info(f"Embedding {len(texts)} articles")
        embeddings = await self.generate_embeddings(texts)
        
        # Add embeddings to articles
        for i, article in enumerate(valid_articles):
            article["embedding"] = embeddings[i].tolist()  # Convert to list for JSON serialization
            article["embedding_model"] = self.model_name
            article["embedding_dim"] = self.embedding_dim
        
        logger.info(f"Successfully embedded {len(valid_articles)} articles")
        return valid_articles
    
    async def compute_similarity(self, 
                               query_embedding: Any,  # np.ndarray when available
                               document_embeddings: Any,  # np.ndarray when available
                               metric: str = "cosine") -> Any:  # Returns np.ndarray when available
        """
        Compute similarity between query and document embeddings.
        
        Args:
            query_embedding: Query embedding (1D array)
            document_embeddings: Document embeddings (2D array)
            metric: Similarity metric ('cosine', 'dot', 'euclidean')
            
        Returns:
            Similarity scores array
        """
        if metric == "cosine":
            # Cosine similarity
            scores = np.dot(document_embeddings, query_embedding)
        elif metric == "dot":
            # Dot product similarity
            scores = np.dot(document_embeddings, query_embedding)
        elif metric == "euclidean":
            # Negative euclidean distance (higher = more similar)
            scores = -np.linalg.norm(document_embeddings - query_embedding, axis=1)
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")
        
        return scores
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Model information dictionary
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dim": self.embedding_dim,
            "model_loaded": self.model is not None,
            "cache_dir": self.cache_dir,
            "available_models": self.DEFAULT_MODELS
        }
    
    async def cleanup(self) -> None:
        """Clean up model resources."""
        if self.model is not None:
            # Clear model from memory
            del self.model
            self.model = None
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda" and torch is not None:
                torch.cuda.empty_cache()
            
            logger.info("Model resources cleaned up")


# Convenience functions for easy usage
async def generate_article_embeddings(articles: List[Dict[str, Any]], 
                                    model_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to generate embeddings for articles.
    
    Args:
        articles: List of article dictionaries
        model_name: Optional model name override
        
    Returns:
        Articles with embeddings added
    """
    generator = EmbeddingGenerator(model_name=model_name)
    
    try:
        return await generator.embed_articles(articles)
    finally:
        await generator.cleanup()


async def test_embedding_generator() -> None:
    """Test function for the embedding generator."""
    print("🧪 Testing Embedding Generator")
    print("=" * 40)
    
    generator = EmbeddingGenerator()
    
    try:
        # Test model loading
        print("Loading model...")
        await generator.load_model()
        print(f"✅ Model loaded: {generator.model_name}")
        print(f"   Embedding dimension: {generator.embedding_dim}")
        print(f"   Device: {generator.device}")
        
        # Test single text embedding
        print("\nTesting single text embedding...")
        test_text = "Artificial intelligence is transforming the technology industry."
        embedding = await generator.generate_embeddings(test_text)
        print(f"✅ Single embedding shape: {embedding.shape}")
        
        # Test batch embedding
        print("\nTesting batch embedding...")
        test_texts = [
            "Machine learning advances in natural language processing",
            "New developments in computer vision and AI",
            "Breakthrough in quantum computing research"
        ]
        embeddings = await generator.generate_embeddings(test_texts)
        print(f"✅ Batch embeddings shape: {embeddings.shape}")
        
        # Test article embedding
        print("\nTesting article embedding...")
        test_articles = [
            {
                "id": 1,
                "title": "AI Research Progress",
                "content": "Recent advances in artificial intelligence research have shown promising results.",
                "source": "test"
            },
            {
                "id": 2,
                "title": "Tech Industry Update",
                "content": "The technology sector continues to evolve with new innovations.",
                "source": "test"
            }
        ]
        
        embedded_articles = await generator.embed_articles(test_articles)
        print(f"✅ Embedded {len(embedded_articles)} articles")
        print(f"   First article embedding shape: {len(embedded_articles[0]['embedding'])}")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise
    finally:
        await generator.cleanup()


if __name__ == "__main__":
    asyncio.run(test_embedding_generator())
