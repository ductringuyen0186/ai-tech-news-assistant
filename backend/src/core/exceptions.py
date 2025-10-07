"""
Custom Exceptions for AI Tech News Assistant
===========================================

This module defines custom exception classes for better error handling
and debugging throughout the application.
"""

import traceback
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for better classification."""
    CONFIGURATION = "configuration"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    SECURITY = "security"


class NewsAssistantError(Exception):
    """
    Base exception class for all application-specific errors.
    
    Provides structured error information for better debugging and monitoring.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        user_message: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details
        self.severity = severity
        self.category = category
        self.user_message = user_message or "An error occurred while processing your request."
        self.retry_after = retry_after  # Seconds to wait before retry
        self.timestamp = datetime.now(timezone.utc)
        self.stack_trace = traceback.format_exc()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "retry_after": self.retry_after
        }


class ConfigurationError(NewsAssistantError):
    """Raised when there are configuration-related issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            user_message="Application configuration error. Please contact support.",
            **kwargs
        )


class DatabaseError(NewsAssistantError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            user_message="Database operation failed. Please try again later.",
            retry_after=5,
            **kwargs
        )


class NotFoundError(NewsAssistantError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: str = "Resource", **kwargs):
        # Merge resource_type into details if provided in kwargs
        existing_details = kwargs.pop('details', {})
        merged_details = {"resource_type": resource_type}
        merged_details.update(existing_details)
        
        super().__init__(
            message=message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.BUSINESS_LOGIC,
            user_message=f"{resource_type} not found.",
            details=merged_details,
            **kwargs
        )


class EmbeddingError(NewsAssistantError):
    """Raised when embedding generation or operations fail."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_API,
            user_message="Embedding processing failed. Please try again.",
            retry_after=10,
            **kwargs
        )


class LLMError(NewsAssistantError):
    """Raised when LLM operations fail."""
    
    def __init__(self, message: str, model: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if model:
            details["model"] = model
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_API,
            user_message="AI processing failed. Please try again.",
            retry_after=15,
            details=details,
            **kwargs
        )


class NewsIngestionError(NewsAssistantError):
    """Raised when news ingestion operations fail."""
    
    def __init__(self, message: str, source: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if source:
            details["source"] = source
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_API,
            user_message="News ingestion failed. Please try again later.",
            retry_after=30,
            details=details,
            **kwargs
        )


class VectorStoreError(NewsAssistantError):
    """Raised when vector store operations fail."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            user_message="Vector database operation failed. Please try again.",
            retry_after=10,
            **kwargs
        )


class ValidationError(NewsAssistantError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        # Extract details from kwargs to avoid conflict
        existing_details = kwargs.pop("details", {})
        if field:
            existing_details["field"] = field
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            user_message="Invalid input provided. Please check your request.",
            details=existing_details,
            **kwargs
        )


class ExternalServiceError(NewsAssistantError):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        details = kwargs.get("details", {})
        if service:
            details["service"] = service
        if status_code:
            details["status_code"] = status_code
        
        # Remove retry_after from kwargs if present to avoid conflict
        retry_after = kwargs.pop("retry_after", 60)
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_API,
            user_message="External service unavailable. Please try again later.",
            retry_after=retry_after,
            details=details,
            **kwargs
        )


class SecurityError(NewsAssistantError):
    """Raised when security-related issues occur."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SECURITY,
            user_message="Access denied.",
            **kwargs
        )


class RateLimitError(NewsAssistantError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_API,
            user_message=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            retry_after=retry_after,
            **kwargs
        )


class TimeoutError(NewsAssistantError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, **kwargs):
        details = kwargs.get("details", {})
        if timeout_duration:
            details["timeout_duration"] = timeout_duration
            
        super().__init__(
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.SYSTEM,
            user_message="Operation timed out. Please try again.",
            retry_after=30,
            details=details,
            **kwargs
        )
