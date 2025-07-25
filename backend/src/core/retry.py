"""
Retry Logic and Circuit Breaker for AI Tech News Assistant
========================================================

This module provides retry mechanisms, exponential backoff, and circuit breaker
patterns for handling transient failures and external service unavailability.
"""

import asyncio
import time
from typing import Any, Callable, Optional, Type, Union, Tuple, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import random

from src.core.logging import get_logger, log_exception
from src.core.exceptions import (
    ExternalServiceError, 
    TimeoutError as CustomTimeoutError, 
    RateLimitError,
    ValidationError,
    NewsAssistantError
)


logger = get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add random jitter to prevent thundering herd
    retry_on: Tuple[Type[Exception], ...] = (
        ExternalServiceError,
        CustomTimeoutError,
        ConnectionError,
        OSError
    )
    stop_on: Tuple[Type[Exception], ...] = (
        RateLimitError,  # Don't retry rate limits immediately
        ValidationError  # Don't retry validation errors
    )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    expected_exception: Type[Exception] = Exception


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    
    When too many failures occur, the circuit "opens" and blocks requests
    for a period to allow the service to recover.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker transitioning to HALF_OPEN for {func.__name__}")
                else:
                    raise ExternalServiceError(
                        f"Circuit breaker is OPEN for {func.__name__}. Service unavailable.",
                        retry_after=self.config.recovery_timeout
                    )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
            
        except self.config.expected_exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    async def _on_success(self):
        """Handle successful operation."""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info("Circuit breaker reset to CLOSED state")
    
    async def _on_failure(self):
        """Handle failed operation."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker opened due to {self.failure_count} failures",
                    extra={"failure_count": self.failure_count, "threshold": self.config.failure_threshold}
                )


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for retry attempt with exponential backoff and jitter."""
    delay = min(
        config.base_delay * (config.exponential_base ** (attempt - 1)),
        config.max_delay
    )
    
    if config.jitter:
        # Add random jitter (±25% of delay)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def should_retry(exception: Exception, config: RetryConfig) -> bool:
    """Determine if an exception should trigger a retry."""
    # Don't retry if explicitly told not to
    if any(isinstance(exception, exc_type) for exc_type in config.stop_on):
        # Special case: if it's a NewsAssistantError but not in stop_on, allow retry
        if isinstance(exception, NewsAssistantError) and type(exception) not in config.stop_on:
            return any(isinstance(exception, exc_type) for exc_type in config.retry_on)
        return False
    
    # Retry if it's in the retry list
    if any(isinstance(exception, exc_type) for exc_type in config.retry_on):
        return True
    
    # For RateLimitError, check if retry_after is reasonable
    if isinstance(exception, RateLimitError):
        return exception.retry_after and exception.retry_after <= 300  # Max 5 minutes
    
    return False


def retry(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        config: Retry configuration. Uses default if None.
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    logger.debug(
                        f"Attempting {func.__name__} (attempt {attempt}/{config.max_attempts})",
                        extra={"attempt": attempt, "max_attempts": config.max_attempts}
                    )
                    
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except Exception as e:
                    last_exception = e
                    
                    if not should_retry(e, config):
                        logger.debug(f"Not retrying {func.__name__} due to exception type: {type(e).__name__}")
                        raise
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"All retry attempts failed for {func.__name__}",
                            extra={"attempts": config.max_attempts, "final_error": str(e)}
                        )
                        raise
                    
                    delay = calculate_delay(attempt, config)
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, retrying in {delay:.2f}s",
                        extra={
                            "attempt": attempt,
                            "delay": delay,
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    )
                    
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # For sync functions, run the async wrapper in a new event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def with_circuit_breaker(config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator for adding circuit breaker protection to functions.
    
    Args:
        config: Circuit breaker configuration. Uses default if None.
    """
    if config is None:
        config = CircuitBreakerConfig()
    
    # Create a circuit breaker instance for this function
    circuit_breaker = CircuitBreaker(config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            return await circuit_breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def resilient(
    retry_config: Optional[RetryConfig] = None,
    circuit_config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator combining retry logic and circuit breaker protection.
    
    Args:
        retry_config: Retry configuration
        circuit_config: Circuit breaker configuration
    """
    def decorator(func: Callable) -> Callable:
        # Apply circuit breaker first, then retry
        if circuit_config:
            func = with_circuit_breaker(circuit_config)(func)
        if retry_config:
            func = retry(retry_config)(func)
        return func
    
    return decorator


# Pre-configured decorators for common scenarios
def external_api_resilient(func: Callable) -> Callable:
    """Decorator for external API calls with appropriate retry and circuit breaker."""
    return resilient(
        retry_config=RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            retry_on=(ExternalServiceError, ConnectionError, CustomTimeoutError)
        ),
        circuit_config=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ExternalServiceError
        )
    )(func)


def database_resilient(func: Callable) -> Callable:
    """Decorator for database operations with retry logic."""
    return retry(
        RetryConfig(
            max_attempts=2,
            base_delay=0.5,
            max_delay=5.0,
            retry_on=(ConnectionError, OSError)
        )
    )(func)


def llm_resilient(func: Callable) -> Callable:
    """Decorator for LLM API calls with appropriate handling."""
    return resilient(
        retry_config=RetryConfig(
            max_attempts=3,
            base_delay=2.0,
            max_delay=60.0,
            retry_on=(ExternalServiceError, CustomTimeoutError)
        ),
        circuit_config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120,
            expected_exception=ExternalServiceError
        )
    )(func)
