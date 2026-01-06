"""
LangChain Multi-Agent System for AI Tech News Assistant
========================================================

This module provides a multi-agent architecture using LangChain for:
- Sequential agent calls (research → analyze → summarize)
- Multi-model orchestration (Groq for speed, Claude for quality)
- Memory management across conversations
- Advanced RAG patterns with self-correction

Features:
- 100% FREE with Groq API (or use free tier of other LLMs)
- Local vector store (ChromaDB) - no cloud costs
- Free HuggingFace embeddings
- Composable agent chains
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_groq import ChatGroq
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    # Using modern LangChain runnable interface
    from langchain_core.runnables import RunnableSequence
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False


class MultiAgentOrchestrator:
    """
    Multi-agent orchestrator using LangChain.
    
    Provides sequential agent execution for complex workflows:
    1. Research Agent - Finds relevant articles from vector store
    2. Analysis Agent - Analyzes trends and patterns
    3. Summarization Agent - Creates comprehensive summaries
    4. QA Agent - Answers specific questions with citations
    """
    
    def __init__(self, 
                 groq_api_key: Optional[str] = None,
                 model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialize the multi-agent orchestrator.
        
        Args:
            groq_api_key: Groq API key (FREE tier available)
            model_name: LLM model to use (Groq models are fastest/cheapest)
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required. Install with: "
                "pip install langchain langchain-groq langchain-chroma langchain-community"
            )
        
        self.groq_api_key = groq_api_key or settings.groq_api_key
        self.model_name = model_name
        
        # Initialize LLM (Groq for speed and low cost)
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name=self.model_name,
            temperature=0.7,
            max_tokens=2048
        )
        
        # Initialize embeddings (FREE HuggingFace models)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",  # Fast, good quality, FREE
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Vector store will be initialized later
        self.vectorstore: Optional[Chroma] = None
        
        # Chat history will be passed directly to methods (no global memory)
        self.chat_history: List[Dict[str, str]] = []
        
        logger.info(f"MultiAgentOrchestrator initialized with {model_name}")

    
    async def initialize_vectorstore(self, persist_directory: str = "./data/chroma_db"):
        """
        Initialize ChromaDB vector store with LangChain integration.
        
        Args:
            persist_directory: Directory for persistent storage (FREE local storage)
        """
        try:
            self.vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings,
                collection_name="news_articles"
            )
            
            count = self.vectorstore._collection.count()
            logger.info(f"Vector store initialized with {count} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def create_research_agent(self) -> RunnableSequence:
        """
        Create research agent that finds relevant articles.
        
        Returns:
            LangChain runnable for research tasks
        """
        research_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research agent for a tech news platform.
Your job is to find and identify the most relevant articles for a given query.

Given a research query, you should:
1. Understand the key topics and keywords
2. Consider related concepts and technologies
3. Formulate search queries that will find relevant articles
4. Return a focused research plan

Be concise but thorough."""),
            ("human", "{query}"),
        ])
        
        return research_prompt | self.llm | StrOutputParser()
    
    def create_analysis_agent(self) -> RunnableSequence:
        """
        Create analysis agent that identifies trends and patterns.
        
        Returns:
            LangChain runnable for analysis tasks
        """
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an analysis agent specialized in technology trends.
Your job is to analyze articles and identify patterns, trends, and insights.

Given article content, you should:
1. Identify key themes and topics
2. Recognize emerging trends
3. Connect related concepts
4. Highlight important developments
5. Provide actionable insights

Be analytical and data-driven."""),
            ("human", "Analyze these articles:\n\n{articles}"),
        ])
        
        return analysis_prompt | self.llm | StrOutputParser()
    
    def create_summarization_agent(self) -> RunnableSequence:
        """
        Create summarization agent for comprehensive summaries.
        
        Returns:
            LangChain runnable for summarization tasks
        """
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a summarization agent for tech news.
Your job is to create clear, concise, and comprehensive summaries.

Given article content and analysis, you should:
1. Extract the most important information
2. Organize information logically
3. Highlight key takeaways
4. Maintain technical accuracy
5. Write in clear, accessible language

Be concise but don't lose important details."""),
            ("human", "Summarize:\n\nArticles: {articles}\n\nAnalysis: {analysis}"),
        ])
        
        return summary_prompt | self.llm | StrOutputParser()
    
    async def research_and_analyze(
        self, 
        query: str, 
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Execute multi-agent workflow: Research → Retrieve → Analyze → Summarize.
        
        This demonstrates sequential agent calls with memory.
        
        Args:
            query: Research query
            top_k: Number of articles to retrieve
            
        Returns:
            Dict with research results, analysis, and summary
        """
        try:
            results = {
                'query': query,
                'timestamp': datetime.utcnow().isoformat(),
                'agents_executed': []
            }
            
            # Step 1: Research Agent - Plan the search
            logger.info("Executing Research Agent...")
            research_agent = self.create_research_agent()
            research_plan = await asyncio.to_thread(
                research_agent.invoke,
                {"query": query}
            )
            results['research_plan'] = research_plan
            results['agents_executed'].append('research')
            
            # Step 2: Retrieval - Get relevant articles from vector store
            logger.info("Retrieving articles from vector store...")
            if self.vectorstore:
                docs = self.vectorstore.similarity_search(query, k=top_k)
                articles_text = "\n\n".join([
                    f"Article {i+1}:\nTitle: {doc.metadata.get('title', 'Unknown')}\n"
                    f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                    f"Content: {doc.page_content[:500]}..."
                    for i, doc in enumerate(docs)
                ])
                results['articles_found'] = len(docs)
                results['articles'] = [
                    {
                        'title': doc.metadata.get('title', 'Unknown'),
                        'source': doc.metadata.get('source', 'Unknown'),
                        'url': doc.metadata.get('url', ''),
                        'snippet': doc.page_content[:200]
                    }
                    for doc in docs
                ]
            else:
                articles_text = "No vector store available. Using general knowledge."
                results['articles_found'] = 0
                results['articles'] = []
            
            # Step 3: Analysis Agent - Analyze trends and patterns
            logger.info("Executing Analysis Agent...")
            analysis_agent = self.create_analysis_agent()
            analysis = await asyncio.to_thread(
                analysis_agent.invoke,
                {"articles": articles_text}
            )
            results['analysis'] = analysis
            results['agents_executed'].append('analysis')
            
            # Step 4: Summarization Agent - Create comprehensive summary
            logger.info("Executing Summarization Agent...")
            summary_agent = self.create_summarization_agent()
            summary = await asyncio.to_thread(
                summary_agent.invoke,
                {"articles": articles_text, "analysis": analysis}
            )
            results['summary'] = summary
            results['agents_executed'].append('summarization')
            
            logger.info(f"Multi-agent workflow completed: {len(results['agents_executed'])} agents executed")
            return results
            
        except Exception as e:
            logger.error(f"Multi-agent workflow failed: {e}")
            return {
                'error': str(e),
                'query': query,
                'agents_executed': results.get('agents_executed', [])
            }
    
    async def conversational_qa(
        self, 
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Conversational Q&A with memory and context.
        
        Args:
            question: User question
            chat_history: Previous conversation history
            
        Returns:
            Answer with sources and context
        """
        try:
            if not self.vectorstore:
                await self.initialize_vectorstore()
            
            # Simple retrieval and answer generation
            docs = await asyncio.to_thread(
                self.vectorstore.similarity_search,
                question,
                k=5
            )
            
            # Format context from retrieved documents
            context = "\n\n".join([
                f"Article: {doc.metadata.get('title', 'Unknown')}\n"
                f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                f"Content: {doc.page_content[:500]}"
                for doc in docs
            ])
            
            # Generate answer using LLM
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful assistant that answers questions about tech news.
                Use the provided context to answer the question accurately.
                If you cannot answer based on the context, say so.
                Always cite the sources you use."""),
                ("human", "Context:\n{context}\n\nQuestion: {question}")
            ])
            
            qa_chain = qa_prompt | self.llm | StrOutputParser()
            answer = await asyncio.to_thread(
                qa_chain.invoke,
                {"context": context, "question": question}
            )
            
            # Format response
            return {
                'question': question,
                'answer': answer,
                'sources': [
                    {
                        'title': doc.metadata.get('title', 'Unknown'),
                        'source': doc.metadata.get('source', 'Unknown'),
                        'url': doc.metadata.get('url', ''),
                    }
                    for doc in result.get('source_documents', [])
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Conversational QA failed: {e}")
            return {
                'question': question,
                'error': str(e)
            }
    
    async def add_articles_to_vectorstore(
        self,
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add articles to vector store using LangChain.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Status and statistics
        """
        try:
            if not self.vectorstore:
                await self.initialize_vectorstore()
            
            # Prepare documents for LangChain
            from langchain_core.documents import Document
            
            documents = []
            for article in articles:
                doc = Document(
                    page_content=f"{article.get('title', '')} {article.get('content', '')}",
                    metadata={
                        'article_id': article.get('id', ''),
                        'title': article.get('title', '')[:500],
                        'source': article.get('source', 'unknown'),
                        'url': article.get('url', ''),
                        'published_at': str(article.get('published_at', '')),
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            await asyncio.to_thread(
                self.vectorstore.add_documents,
                documents
            )
            
            return {
                'success': True,
                'documents_added': len(documents),
                'total_documents': self.vectorstore._collection.count()
            }
            
        except Exception as e:
            logger.error(f"Failed to add articles to vector store: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
_orchestrator: Optional[MultiAgentOrchestrator] = None


async def get_agent_orchestrator() -> MultiAgentOrchestrator:
    """
    Get or create the singleton agent orchestrator.
    
    Returns:
        Initialized MultiAgentOrchestrator
    """
    global _orchestrator
    
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
        await _orchestrator.initialize_vectorstore()
    
    return _orchestrator
