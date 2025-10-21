"""
Groq Provider for Fast LLM Inference
===================================

Groq provides ultra-fast inference for open-source models like Llama 3.2.
Perfect for portfolio projects - generous free tier with no credit card required.

Features:
- 500+ tokens/second (faster than GPT-4)
- Free tier: 30 requests/minute
- Compatible with OpenAI SDK
- Best for: Demos, prototypes, portfolio projects

Sign up: https://console.groq.com
"""

import httpx
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class GroqProvider:
    """
    Groq provider for ultra-fast LLM inference.
    
    Uses Groq's LPU (Language Processing Unit) for blazing-fast inference.
    Free tier: 30 requests/minute - perfect for portfolio projects.
    """
    
    AVAILABLE_MODELS = {
        "llama-3.2-1b-preview": "Fastest, most efficient (1B params)",
        "llama-3.2-3b-preview": "Balance of speed and quality (3B params)",
        "llama3-8b-8192": "High quality, still fast (8B params)",
        "llama3-70b-8192": "Best quality (70B params, slower)",
        "mixtral-8x7b-32768": "Good for complex tasks",
    }
    
    def __init__(self,
                 api_key: str,
                 model: str = "llama-3.2-3b-preview",
                 timeout: int = 30):
        """
        Initialize Groq provider.
        
        Args:
            api_key: Groq API key (get from https://console.groq.com)
            model: Model to use (default: llama-3.2-3b-preview)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.groq.com/openai/v1"
        
        if model not in self.AVAILABLE_MODELS:
            logger.warning(f"Model {model} not in known models. Using anyway.")
        
        logger.info(f"Initialized Groq provider with model: {model}")
    
    async def is_available(self) -> bool:
        """Check if Groq API is accessible."""
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            logger.warning("Groq API key not configured")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    logger.info("Groq API is available")
                    return True
                else:
                    logger.warning(f"Groq API returned status: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking Groq availability: {str(e)}")
            return False
    
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Summarize text using Groq's ultra-fast LLM inference.
        
        Args:
            text: Article text to summarize
            **kwargs: Additional parameters (max_length, temperature, etc.)
            
        Returns:
            Dict with summary, keywords, and metadata
        """
        try:
            # Validate input
            if not text or len(text.strip()) == 0:
                logger.warning("Empty text provided for summarization")
                return {
                    "success": False,
                    "error": "Empty text provided"
                }
            
            # Truncate if too long (Groq has context limits)
            max_input_length = kwargs.get("max_input_length", 6000)
            if len(text) > max_input_length:
                logger.info(f"Truncating input from {len(text)} to {max_input_length} chars")
                text = text[:max_input_length] + "..."
            
            # Build prompt
            max_summary_length = kwargs.get("max_length", 200)
            prompt = self._build_summary_prompt(text, max_summary_length)
            
            # Call Groq API (OpenAI-compatible)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a tech news summarization expert. Provide concise, informative summaries."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 500),
                        "top_p": kwargs.get("top_p", 0.9),
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }
                
                result = response.json()
                
                # Extract summary
                summary = result["choices"][0]["message"]["content"].strip()
                
                # Extract keywords (simple approach - you can enhance this)
                keywords = self._extract_keywords(summary)
                
                logger.info(f"Successfully summarized text with Groq ({self.model})")
                
                return {
                    "success": True,
                    "summary": summary,
                    "keywords": keywords,
                    "model": self.model,
                    "provider": "groq",
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    "response_time": result.get("response_time", 0)
                }
                
        except httpx.TimeoutException:
            logger.error("Groq API request timed out")
            return {
                "success": False,
                "error": "Request timed out"
            }
        except Exception as e:
            logger.error(f"Error in Groq summarization: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_summary_prompt(self, text: str, max_length: int) -> str:
        """Build the summarization prompt."""
        return f"""Summarize the following tech news article in {max_length} words or less.
Focus on:
1. Key technical points and innovations
2. Important implications for the tech industry
3. Main takeaways for developers/engineers

Article:
{text}

Summary:"""
    
    def _extract_keywords(self, text: str) -> list:
        """
        Extract keywords from text (simple implementation).
        You can enhance this with NLP libraries if needed.
        """
        # Simple keyword extraction - look for tech terms
        tech_keywords = [
            "AI", "ML", "API", "cloud", "database", "framework",
            "algorithm", "model", "GPU", "CPU", "deployment",
            "architecture", "performance", "security", "scalability"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in tech_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # Return top 10
    
    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """
        Generic chat completion (for future AI agent features).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Dict with response and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 1000),
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }
                
                result = response.json()
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"],
                    "model": self.model,
                    "provider": "groq"
                }
                
        except Exception as e:
            logger.error(f"Error in Groq chat: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Convenience function to create Groq provider from settings
def create_groq_provider() -> GroqProvider:
    """Create Groq provider from application settings."""
    return GroqProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        timeout=settings.llm_timeout
    )
