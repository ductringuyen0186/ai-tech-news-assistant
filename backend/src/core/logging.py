"""
Logging Configuration for AI Tech News Assistant
===============================================

This module provides structured logging configuration for the application.
It supports different log levels and formats for development and production,
correlation IDs for request tracing, and integration with monitoring systems.
"""

import json
import logging
import sys
import contextvars
from typing import Optional, Dict, Any, Union
from datetime import datetime
import uuid

from src.core.config import get_settings
from src.core.exceptions import NewsAssistantError


# Context variable for correlation ID (request tracing)
correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id', default='')


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for production logging.
    
    Adds correlation IDs, structured error information, and consistent format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(),
        }
        
        # Add module and function information
        if hasattr(record, 'pathname'):
            log_entry["module"] = record.pathname
        if hasattr(record, 'funcName'):
            log_entry["function"] = record.funcName
        if hasattr(record, 'lineno'):
            log_entry["line"] = record.lineno
            
        # Add request information if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'endpoint'):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_entry["method"] = record.method
            
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_entry["duration_ms"] = record.duration
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
            
        # Handle exceptions with structured information
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            log_entry["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "traceback": self.formatException(record.exc_info) if exc_traceback else None
            }
            
            # Add structured error information for custom exceptions
            if isinstance(exc_value, NewsAssistantError):
                log_entry["error_details"] = exc_value.to_dict()
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                if not key.startswith('_'):
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    
    Includes colors and correlation IDs for better debugging experience.
    """
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Add correlation ID to the record
        corr_id = correlation_id.get()
        if corr_id:
            record.correlation_id = corr_id[:8]  # Short version for readability
        else:
            record.correlation_id = ""
            
        # Apply color to log level
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            
        return super().format(record)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    settings = get_settings()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper()))
        
        # Choose formatter based on environment
        if settings.environment == "production":
            formatter = StructuredFormatter()
        else:
            # Development format with correlation ID
            dev_format = "%(asctime)s | %(correlation_id)-8s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
            formatter = DevelopmentFormatter(dev_format)
            
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger


def setup_logging() -> None:
    """Setup application-wide logging configuration."""
    settings = get_settings()
    
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Choose formatter based on environment
    if settings.environment == "production":
        formatter = StructuredFormatter()
    else:
        # Development format
        dev_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        formatter = DevelopmentFormatter(dev_format)
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Suppress verbose logs from external libraries in production
    if settings.environment == "production":
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("chromadb").setLevel(logging.WARNING)
    
    # Add a startup log message
    logger = get_logger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "environment": settings.environment,
            "log_level": settings.log_level,
            "app_name": settings.app_name
        }
    )


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """
    Set correlation ID for request tracing.
    
    Args:
        corr_id: Optional correlation ID. If None, generates a new UUID.
        
    Returns:
        The correlation ID that was set
    """
    if corr_id is None:
        corr_id = str(uuid.uuid4())
    
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return correlation_id.get()


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    **extra_fields
) -> None:
    """
    Log an exception with structured information.
    
    Args:
        logger: Logger instance
        exception: Exception to log
        message: Custom message
        **extra_fields: Additional fields to include in log
    """
    extra = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        **extra_fields
    }
    
    # Add structured error information for custom exceptions
    if isinstance(exception, NewsAssistantError):
        extra.update(exception.to_dict())
    
    logger.error(message, exc_info=True, extra=extra)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **extra_fields
) -> None:
    """
    Log performance metrics.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        success: Whether operation was successful
        **extra_fields: Additional fields
    """
    level = logging.INFO if success else logging.WARNING
    
    extra = {
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success,
        **extra_fields
    }
    
    logger.log(level, f"Operation completed: {operation}", extra=extra)


def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    **extra_fields
) -> None:
    """
    Log API request information.
    
    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
        **extra_fields: Additional fields
    """
    level = logging.INFO if status_code < 400 else logging.WARNING
    
    extra = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **extra_fields
    }
    
    if user_id:
        extra["user_id"] = user_id
    
    message = f"{method} {endpoint} - {status_code} ({duration_ms:.2f}ms)"
    logger.log(level, message, extra=extra)
