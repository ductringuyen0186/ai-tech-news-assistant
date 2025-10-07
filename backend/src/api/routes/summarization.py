"""
Summarization Routes
==================

API routes for AI-powered content summarization using LLM providers.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from ...services import SummarizationService
from ...repositories import ArticleRepository
from ...models.article import SummarizationRequest, ArticleSummary
from ...models.api import BaseResponse, AsyncTaskResponse
from ...core.exceptions import LLMError, ValidationError

router = APIRouter(prefix="/summarize", tags=["Summarization"])

# Dependency injection
def get_summarization_service() -> SummarizationService:
    """Get summarization service instance."""
    return SummarizationService()

def get_article_repository() -> ArticleRepository:
    """Get article repository instance."""
    return ArticleRepository()


@router.post("/", response_model=BaseResponse[ArticleSummary])
async def summarize_content(
    request: SummarizationRequest,
    service: SummarizationService = Depends(get_summarization_service)
) -> BaseResponse[ArticleSummary]:
    """
    Generate a summary for the provided content using LLM.
    
    Args:
        request: Summarization request with content and parameters
        
    Returns:
        Generated summary with metadata
        
    Raises:
        HTTPException: If summarization fails
    """
    try:
        # Generate summary using service
        summary = await service.summarize_content(request)
        
        return BaseResponse(
            success=True,
            message="Content summarized successfully",
            data=summary
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except LLMError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/article/{article_id}", response_model=BaseResponse[ArticleSummary])
async def summarize_article(
    article_id: int,
    max_length: int = 500,
    style: str = "paragraph",
    service: SummarizationService = Depends(get_summarization_service),
    repo: ArticleRepository = Depends(get_article_repository)
) -> BaseResponse[ArticleSummary]:
    """
    Generate a summary for a specific article.
    
    Args:
        article_id: ID of the article to summarize
        max_length: Maximum length of the summary
        style: Summary style ('paragraph' or 'bullet_points')
        
    Returns:
        Generated summary for the article
    """
    try:
        # Get article from repository
        article = await repo.get_by_id(article_id)
        
        if not article.content:
            raise HTTPException(
                status_code=400,
                detail="Article has no content to summarize"
            )
        
        # Create summarization request
        request = SummarizationRequest(
            content=article.content,
            max_length=max_length,
            style=style
        )
        
        # Generate summary
        summary = await service.summarize_content(request)
        
        # Update article with summary (optional - could be done separately)
        from ...models.article import ArticleUpdate
        update_data = ArticleUpdate(summary=summary.summary)
        await repo.update(article_id, update_data)
        
        return BaseResponse(
            success=True,
            message=f"Article {article_id} summarized successfully",
            data=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize article: {str(e)}")


@router.post("/batch", response_model=BaseResponse[List[ArticleSummary]])
async def batch_summarize(
    requests: List[SummarizationRequest],
    service: SummarizationService = Depends(get_summarization_service)
) -> BaseResponse[List[ArticleSummary]]:
    """
    Generate summaries for multiple content pieces.
    
    Args:
        requests: List of summarization requests (max 10)
        
    Returns:
        List of generated summaries
    """
    try:
        if len(requests) > 10:
            raise HTTPException(
                status_code=400,
                detail="Too many requests. Maximum 10 items per batch."
            )
        
        summaries = await service.batch_summarize(requests)
        
        return BaseResponse(
            success=True,
            message=f"Batch summarization completed. Generated {len(summaries)} summaries.",
            data=summaries
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch summarization failed: {str(e)}")


@router.post("/articles/auto", response_model=AsyncTaskResponse)
async def auto_summarize_articles(
    limit: int = 50,
    only_without_summary: bool = True,
    service: SummarizationService = Depends(get_summarization_service),
    repo: ArticleRepository = Depends(get_article_repository)
) -> AsyncTaskResponse:
    """
    Automatically generate summaries for articles that don't have them.
    
    Args:
        limit: Maximum number of articles to process
        only_without_summary: Only process articles without existing summaries
        
    Returns:
        Async task information for tracking progress
    """
    try:
        # This would typically be implemented as a background task
        # For now, we'll return a placeholder response
        
        import uuid
        task_id = str(uuid.uuid4())
        
        return AsyncTaskResponse(
            task_id=task_id,
            status="initiated",
            progress_percentage=0.0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start auto-summarization: {str(e)}"
        )


@router.get("/status", response_model=BaseResponse[Dict[str, Any]])
async def get_summarization_status(
    service: SummarizationService = Depends(get_summarization_service)
) -> BaseResponse[Dict[str, Any]]:
    """
    Get the status of the summarization service and available providers.
    
    Returns:
        Service status and provider information
    """
    try:
        status = await service.health_check()
        
        return BaseResponse(
            success=True,
            message="Summarization service status retrieved",
            data=status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.get("/providers", response_model=BaseResponse[Dict[str, Any]])
async def get_available_providers(
    service: SummarizationService = Depends(get_summarization_service)
) -> BaseResponse[Dict[str, Any]]:
    """
    Get information about available LLM providers for summarization.
    
    Returns:
        Available providers and their status
    """
    try:
        status = await service.health_check()
        providers = status.get("providers", {})
        
        return BaseResponse(
            success=True,
            message="Provider information retrieved",
            data={
                "available_providers": list(providers.keys()),
                "provider_details": providers
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get provider information: {str(e)}"
        )
