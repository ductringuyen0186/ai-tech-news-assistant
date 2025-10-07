"""
AI Service - LLM Integration for Summarization & Classification
================================================================
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings
from ..models.user import TechCategory

logger = logging.getLogger(__name__)


class AIService:
    """AI service for summarization, classification, and analysis"""

    def __init__(self):
        self.ollama_base = settings.OLLAMA_HOST
        self.ollama_model = settings.OLLAMA_MODEL
        self.use_ollama = True  # Will fallback if Ollama unavailable

        # Category keywords for classification
        self.category_keywords = {
            TechCategory.AI_ML: [
                "ai", "artificial intelligence", "machine learning", "ml", "deep learning",
                "neural network", "gpt", "llm", "chatgpt", "openai", "anthropic", "claude",
                "tensorflow", "pytorch", "transformer", "diffusion", "generative"
            ],
            TechCategory.SOFTWARE_DEV: [
                "programming", "developer", "coding", "software", "api", "framework",
                "library", "javascript", "python", "rust", "go", "java", "typescript",
                "git", "github", "devops", "agile", "microservices"
            ],
            TechCategory.BIG_TECH: [
                "google", "microsoft", "apple", "amazon", "meta", "facebook", "netflix",
                "tesla", "nvidia", "intel", "amd", "ibm", "oracle", "salesforce"
            ],
            TechCategory.MILITARY_TECH: [
                "military", "defense", "drone", "warfare", "pentagon", "army", "navy",
                "air force", "cyber warfare", "missile", "radar", "surveillance"
            ],
            TechCategory.HOME_TECH: [
                "smart home", "iot", "alexa", "google home", "nest", "smart speaker",
                "home automation", "smart thermostat", "smart lock", "ring", "ecobee"
            ],
            TechCategory.AUTO_TECH: [
                "autonomous", "self-driving", "electric vehicle", "ev", "tesla", "waymo",
                "cruise", "automotive", "car tech", "lidar", "battery", "charging"
            ],
            TechCategory.BLOCKCHAIN: [
                "blockchain", "crypto", "bitcoin", "ethereum", "web3", "nft", "defi",
                "smart contract", "cryptocurrency", "solana", "polygon"
            ],
            TechCategory.CYBERSECURITY: [
                "security", "cybersecurity", "hacking", "vulnerability", "breach",
                "encryption", "zero-day", "malware", "ransomware", "firewall"
            ],
            TechCategory.CLOUD: [
                "cloud", "aws", "azure", "gcp", "google cloud", "serverless", "kubernetes",
                "docker", "container", "iaas", "paas", "saas"
            ],
            TechCategory.ROBOTICS: [
                "robot", "robotics", "automation", "industrial robot", "humanoid",
                "boston dynamics", "drone", "autonomous system"
            ],
            TechCategory.QUANTUM: [
                "quantum", "quantum computing", "qubit", "quantum supremacy",
                "quantum algorithm", "ibm quantum"
            ],
            TechCategory.BIOTECH: [
                "biotech", "crispr", "gene editing", "dna", "genomics", "bioinformatics",
                "synthetic biology", "mrna", "protein folding"
            ],
            TechCategory.FINTECH: [
                "fintech", "payment", "banking", "stripe", "paypal", "square",
                "digital wallet", "buy now pay later", "bnpl", "neobank"
            ],
            TechCategory.GAMING: [
                "gaming", "game", "esports", "xbox", "playstation", "nintendo",
                "unity", "unreal engine", "steam", "twitch"
            ],
            TechCategory.AR_VR: [
                "ar", "vr", "augmented reality", "virtual reality", "metaverse",
                "oculus", "quest", "hololens", "mixed reality", "spatial computing"
            ],
            TechCategory.SPACE_TECH: [
                "space", "spacex", "nasa", "satellite", "rocket", "mars", "moon",
                "starlink", "blue origin", "astronomy"
            ],
            TechCategory.GREEN_TECH: [
                "green tech", "renewable", "solar", "wind", "climate", "sustainability",
                "carbon", "clean energy", "electric", "battery"
            ],
            TechCategory.STARTUP: [
                "startup", "vc", "venture capital", "funding", "series a", "series b",
                "unicorn", "ipo", "y combinator", "acquisition"
            ]
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_base}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    async def summarize_text(
        self,
        text: str,
        max_length: int = 150,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """Summarize text using AI or extractive methods"""

        # Try AI summarization if requested and available
        if use_ai and self.use_ollama:
            ai_summary = await self._ai_summarize(text, max_length)
            if ai_summary:
                return {
                    "summary": ai_summary,
                    "method": "ai_ollama",
                    "model": self.ollama_model,
                    "success": True
                }

        # Fallback to extractive summarization
        return self._extractive_summarize(text, max_length)

    async def _ai_summarize(self, text: str, max_length: int) -> Optional[str]:
        """AI-powered summarization using Ollama"""
        try:
            # Check if Ollama is available
            if not await self.check_ollama_availability():
                logger.warning("Ollama unavailable, falling back to extractive")
                return None

            prompt = f"""Summarize the following tech news article in {max_length} characters or less.
Be concise and focus on the key points. Do not include any preamble, just the summary.

Article:
{text[:1000]}

Summary:"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    summary = result.get("response", "").strip()

                    # Truncate if needed
                    if len(summary) > max_length:
                        summary = summary[:max_length-3] + "..."

                    return summary

        except Exception as e:
            logger.error(f"AI summarization failed: {e}")

        return None

    def _extractive_summarize(self, text: str, max_length: int) -> Dict[str, Any]:
        """Fallback extractive summarization"""
        sentences = text.split('. ')

        if len(sentences) >= 3:
            summary = '. '.join(sentences[:2]) + '.'
            method = "extractive_multi"
        elif len(sentences) >= 2:
            summary = '. '.join(sentences[:2]) + '.'
            method = "extractive_dual"
        else:
            summary = sentences[0] + '.' if sentences else text[:max_length]
            method = "extractive_single"

        # Truncate if needed
        if len(summary) > max_length:
            words = summary.split()
            summary = ' '.join(words[:30]) + '...'
            method += "_truncated"

        return {
            "summary": summary,
            "method": method,
            "model": "extractive",
            "success": True
        }

    async def classify_article(self, title: str, content: str) -> List[str]:
        """Classify article into tech categories"""

        # Try AI classification first
        ai_categories = await self._ai_classify(title, content)
        if ai_categories:
            return ai_categories

        # Fallback to keyword-based classification
        return self._keyword_classify(title, content)

    async def _ai_classify(self, title: str, content: str) -> Optional[List[str]]:
        """AI-powered classification using Ollama"""
        try:
            if not await self.check_ollama_availability():
                return None

            categories_list = ", ".join([cat.value for cat in TechCategory])

            prompt = f"""Classify this tech news article into one or more categories from this list:
{categories_list}

Return ONLY a JSON array of category values, nothing else.

Title: {title}
Content: {content[:500]}

Categories:"""

            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()

                    # Try to parse JSON response
                    try:
                        # Extract JSON array from response
                        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                        if json_match:
                            categories = json.loads(json_match.group())
                            # Validate categories
                            valid_cats = [c for c in categories if c in [cat.value for cat in TechCategory]]
                            if valid_cats:
                                return valid_cats[:3]  # Max 3 categories
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            logger.error(f"AI classification failed: {e}")

        return None

    def _keyword_classify(self, title: str, content: str) -> List[str]:
        """Keyword-based fallback classification"""
        text = (title + " " + content).lower()
        category_scores = {}

        # Calculate score for each category
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category.value] = score

        # Sort by score and return top 3
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [cat for cat, _ in sorted_categories[:3]] if sorted_categories else ["general"]

    async def extract_keywords(self, title: str, content: str, max_keywords: int = 10) -> List[str]:
        """Extract key terms from article"""

        # Try AI extraction first
        ai_keywords = await self._ai_extract_keywords(title, content, max_keywords)
        if ai_keywords:
            return ai_keywords

        # Fallback to simple extraction
        return self._simple_keyword_extract(title, content, max_keywords)

    async def _ai_extract_keywords(self, title: str, content: str, max_keywords: int) -> Optional[List[str]]:
        """AI-powered keyword extraction"""
        try:
            if not await self.check_ollama_availability():
                return None

            prompt = f"""Extract {max_keywords} key technical terms/keywords from this article.
Return ONLY a JSON array of keywords, nothing else.

Title: {title}
Content: {content[:500]}

Keywords:"""

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()

                    # Try to parse JSON
                    try:
                        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                        if json_match:
                            keywords = json.loads(json_match.group())
                            return [kw.lower().strip() for kw in keywords[:max_keywords]]
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            logger.error(f"AI keyword extraction failed: {e}")

        return None

    def _simple_keyword_extract(self, title: str, content: str, max_keywords: int) -> List[str]:
        """Simple keyword extraction fallback"""
        # Combine title and content
        text = title + " " + content

        # Common tech terms to look for
        tech_terms = set()
        all_keywords = []

        for keywords in self.category_keywords.values():
            all_keywords.extend(keywords)

        # Find matching tech terms
        for keyword in all_keywords:
            if keyword in text.lower():
                tech_terms.add(keyword)

        # Return top keywords
        return list(tech_terms)[:max_keywords]

    async def analyze_sentiment(self, title: str, content: str) -> str:
        """Analyze sentiment of article"""

        # Try AI sentiment analysis
        ai_sentiment = await self._ai_sentiment(title, content)
        if ai_sentiment:
            return ai_sentiment

        # Fallback to simple sentiment
        return self._simple_sentiment(title, content)

    async def _ai_sentiment(self, title: str, content: str) -> Optional[str]:
        """AI-powered sentiment analysis"""
        try:
            if not await self.check_ollama_availability():
                return None

            prompt = f"""Analyze the sentiment of this tech news article.
Respond with ONLY one word: positive, negative, or neutral.

Title: {title}
Content: {content[:300]}

Sentiment:"""

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    sentiment = result.get("response", "").strip().lower()

                    if sentiment in ["positive", "negative", "neutral"]:
                        return sentiment

        except Exception as e:
            logger.error(f"AI sentiment analysis failed: {e}")

        return None

    def _simple_sentiment(self, title: str, content: str) -> str:
        """Simple sentiment analysis fallback"""
        text = (title + " " + content).lower()

        positive_words = ["breakthrough", "success", "innovation", "launch", "new", "improve", "better", "growth", "advance"]
        negative_words = ["fail", "breach", "hack", "vulnerability", "problem", "issue", "concern", "risk", "threat"]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

    async def enrich_article(self, title: str, content: str) -> Dict[str, Any]:
        """Complete AI enrichment of article"""

        logger.info(f"Enriching article: {title[:50]}...")

        # Run all analysis in parallel where possible
        summary_task = self.summarize_text(content, max_length=200, use_ai=True)
        categories_task = self.classify_article(title, content)
        keywords_task = self.extract_keywords(title, content, max_keywords=8)
        sentiment_task = self.analyze_sentiment(title, content)

        # Await all tasks
        summary_result = await summary_task
        categories = await categories_task
        keywords = await keywords_task
        sentiment = await sentiment_task

        enrichment = {
            "ai_summary": summary_result.get("summary"),
            "summary_method": summary_result.get("method"),
            "categories": categories,
            "keywords": keywords,
            "sentiment": sentiment,
            "enriched_at": "utcnow"
        }

        logger.info(f"Article enriched: {len(categories)} categories, {len(keywords)} keywords")

        return enrichment


# Global AI service instance
ai_service = AIService()
