"""
Error Handling Middleware for AI Tech News Assistant
==================================================

This module provides comprehensive error handling middleware for FastAPI
including structured error responses, logging, and monitoring integration.
"""

import time
from typing import Dict, Any, Optional
from uuid import uuid4

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.logging import get_logger, set_correlation_id, log_api_request, log_exception
from src.core.exceptions import (
    NewsAssistantError,
    ValidationError,
    NotFoundError,
    ExternalServiceError,
    SecurityError,
    RateLimitError,
    ErrorSeverity
)


logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling errors and logging requests.
    
    Provides:
    - Correlation ID generation and tracking
    - Structured error responses
    - Performance monitoring
    - Error logging with context
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate correlation ID for request tracing
        correlation_id = str(uuid4())
        set_correlation_id(correlation_id)
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Record start time for performance monitoring
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful request
            log_api_request(
                logger=logger,
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=getattr(request.state, 'user_id', None)
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            # Calculate duration for failed requests too
            duration_ms = (time.time() - start_time) * 1000
            
            # Handle the exception and create appropriate response
            error_response = await self._handle_exception(
                request=request,
                exception=exc,
                duration_ms=duration_ms
            )
            
            # Add correlation ID to error response headers
            error_response.headers["X-Correlation-ID"] = correlation_id
            
            return error_response
    
    async def _handle_exception(
        self, 
        request: Request, 
        exception: Exception,
        duration_ms: float
    ) -> JSONResponse:
        """Handle different types of exceptions and return appropriate responses."""
        
        # Determine error details based on exception type
        if isinstance(exception, NewsAssistantError):
            status_code = self._get_status_code_for_custom_error(exception)
            error_response = self._create_error_response(
                error=exception,
                status_code=status_code,
                correlation_id=request.state.correlation_id
            )
            log_level = "warning" if exception.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM] else "error"
            
        elif isinstance(exception, HTTPException):
            status_code = exception.status_code
            error_response = self._create_http_error_response(
                exception=exception,
                correlation_id=request.state.correlation_id
            )
            log_level = "warning" if status_code < 500 else "error"
            
        else:
            # Unhandled exception
            status_code = 500
            error_response = self._create_generic_error_response(
                exception=exception,
                correlation_id=request.state.correlation_id
            )
            log_level = "error"
        
        # Log the error with context
        extra_context = {
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": getattr(request.state, 'user_id', None),
            "user_agent": request.headers.get("user-agent"),
            "ip_address": self._get_client_ip(request)
        }
        
        if log_level == "error":
            log_exception(
                logger=logger,
                exception=exception,
                message=f"Request failed: {request.method} {request.url.path}",
                **extra_context
            )
        else:
            logger.warning(
                f"Request warning: {request.method} {request.url.path} - {status_code}",
                extra=extra_context
            )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    def _get_status_code_for_custom_error(self, error: NewsAssistantError) -> int:
        """Map custom errors to appropriate HTTP status codes."""
        error_status_map = {
            ValidationError: 400,
            NotFoundError: 404,
            SecurityError: 403,
            RateLimitError: 429,
            ExternalServiceError: 502,
        }
        
        return error_status_map.get(type(error), 500)
    
    def _create_error_response(
        self, 
        error: NewsAssistantError, 
        status_code: int,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Create structured error response for custom errors."""
        response = {
            "error": {
                "code": error.error_code,
                "message": error.user_message,
                "details": error.details,
                "correlation_id": correlation_id,
                "timestamp": error.timestamp.isoformat()
            }
        }
        
        # Add retry information if available
        if error.retry_after:
            response["error"]["retry_after"] = error.retry_after
        
        # Add severity for monitoring (but not expose to users)
        if hasattr(error, 'severity'):
            response["error"]["_severity"] = error.severity.value
        
        return response
    
    def _create_http_error_response(
        self, 
        exception: HTTPException,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Create error response for HTTP exceptions."""
        return {
            "error": {
                "code": f"HTTP_{exception.status_code}",
                "message": exception.detail,
                "correlation_id": correlation_id,
                "timestamp": time.time()
            }
        }
    
    def _create_generic_error_response(
        self, 
        exception: Exception,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Create error response for unhandled exceptions."""
        return {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "correlation_id": correlation_id,
                "timestamp": time.time()
            }
        }
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for proxy/load balancer setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return None


def create_custom_error_handlers():
    """Create custom error handlers for specific exception types."""
    
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors with detailed field information."""
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.details,
                    "correlation_id": getattr(request.state, 'correlation_id', ''),
                    "timestamp": exc.timestamp.isoformat()
                }
            }
        )
    
    async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """Handle resource not found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": exc.user_message,
                    "details": exc.details,
                    "correlation_id": getattr(request.state, 'correlation_id', ''),
                    "timestamp": exc.timestamp.isoformat()
                }
            }
        )
    
    async def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
        """Handle rate limit errors with retry information."""
        response = JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": exc.user_message,
                    "retry_after": exc.retry_after,
                    "correlation_id": getattr(request.state, 'correlation_id', ''),
                    "timestamp": exc.timestamp.isoformat()
                }
            }
        )
        
        # Add Retry-After header as per HTTP standard
        if exc.retry_after:
            response.headers["Retry-After"] = str(exc.retry_after)
        
        return response
    
    return {
        ValidationError: validation_error_handler,
        NotFoundError: not_found_error_handler,
        RateLimitError: rate_limit_error_handler,
    }


# Health check middleware for monitoring
class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware for health check monitoring.
    
    Tracks application health metrics and provides endpoints for monitoring.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip health check endpoints to avoid recursive metrics
        if request.url.path in ["/health", "/ping", "/metrics"]:
            return await call_next(request)
        
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = await call_next(request)
            
            # Track response time
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Track errors
            if response.status_code >= 400:
                self.error_count += 1
            
            return response
            
        except Exception:
            self.error_count += 1
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get health metrics."""
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0
        )
        error_rate = (
            self.error_count / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "average_response_time": avg_response_time
        }
