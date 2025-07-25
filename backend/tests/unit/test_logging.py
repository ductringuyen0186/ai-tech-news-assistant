"""
Unit Tests for Core Logging
===========================

Tests for logging configuration and functionality.
"""

import pytest
import logging
import io
import sys
from unittest.mock import patch, MagicMock
from contextlib import redirect_stderr

from src.core.logging import setup_logging, get_logger


class TestLoggingSetup:
    """Test cases for logging setup and configuration."""
    
    def test_setup_logging_development(self):
        """Test logging setup for development environment."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'development'
            mock_settings.debug = True
            mock_settings.log_level = 'DEBUG'
            mock_settings.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
            setup_logging()
            
            # Get root logger and check configuration
            logger = logging.getLogger()
            assert logger.level == logging.DEBUG
            
            # Check that handlers are configured
            assert len(logger.handlers) > 0
    
    def test_setup_logging_production(self):
        """Test logging setup for production environment."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'production'
            mock_settings.debug = False
            mock_settings.log_level = 'INFO'
            mock_settings.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
            setup_logging()
            
            # Get root logger and check configuration
            logger = logging.getLogger()
            assert logger.level == logging.INFO
    
    def test_setup_logging_with_file_handler(self):
        """Test logging setup with file handler configuration."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'production'
            mock_settings.debug = False
            mock_settings.log_level = 'INFO'
            mock_settings.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            mock_settings.log_file = 'app.log'
            
            with patch('logging.FileHandler') as mock_file_handler:
                setup_logging()
                
                # Verify file handler was created
                mock_file_handler.assert_called_once_with('app.log')
    
    def test_setup_logging_json_format(self):
        """Test logging setup with JSON format."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'production'
            mock_settings.debug = False
            mock_settings.log_level = 'INFO'
            mock_settings.log_format = 'json'
            
            setup_logging()
            
            # Should not raise any errors
            logger = logging.getLogger()
            assert logger.level == logging.INFO
    
    def test_get_logger_with_name(self):
        """Test getting logger with specific name."""
        logger = get_logger('test.module')
        
        assert logger.name == 'test.module'
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_without_name(self):
        """Test getting logger without specifying name."""
        logger = get_logger()
        
        assert logger.name == 'root'
        assert isinstance(logger, logging.Logger)
    
    def test_structured_logging(self):
        """Test structured logging functionality."""
        # Capture log output
        log_capture = io.StringIO()
        
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'production'
            mock_settings.debug = False
            mock_settings.log_level = 'INFO'
            mock_settings.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
            # Setup logging with custom handler
            setup_logging()
            
            logger = get_logger('test')
            
            # Add our test handler
            handler = logging.StreamHandler(log_capture)
            handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Test different log levels
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Check output
            output = log_capture.getvalue()
            assert "INFO - Info message" in output
            assert "WARNING - Warning message" in output
            assert "ERROR - Error message" in output
    
    def test_logger_context_information(self):
        """Test logging with context information."""
        log_capture = io.StringIO()
        
        logger = get_logger('test.context')
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Log with extra context
        logger.info("Processing request", extra={
            'user_id': 'user123',
            'request_id': 'req456'
        })
        
        output = log_capture.getvalue()
        assert "test.context - INFO - Processing request" in output
    
    def test_exception_logging(self):
        """Test logging of exceptions with traceback."""
        log_capture = io.StringIO()
        
        logger = get_logger('test.exception')
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        try:
            # Generate an exception
            1 / 0
        except ZeroDivisionError:
            logger.exception("Division by zero occurred")
        
        output = log_capture.getvalue()
        assert "ERROR - Division by zero occurred" in output
        assert "ZeroDivisionError" in output
        assert "Traceback" in output
    
    def test_log_filtering(self):
        """Test log filtering functionality."""
        log_capture = io.StringIO()
        
        logger = get_logger('test.filter')
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)  # Only WARNING and above
        
        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        output = log_capture.getvalue()
        assert "Debug message" not in output
        assert "Info message" not in output
        assert "WARNING - Warning message" in output
        assert "ERROR - Error message" in output
    
    def test_multiple_handlers(self):
        """Test logging with multiple handlers."""
        console_capture = io.StringIO()
        file_capture = io.StringIO()
        
        logger = get_logger('test.multi')
        
        # Add console handler
        console_handler = logging.StreamHandler(console_capture)
        console_handler.setFormatter(logging.Formatter('CONSOLE: %(message)s'))
        logger.addHandler(console_handler)
        
        # Add file handler (simulated with StringIO)
        file_handler = logging.StreamHandler(file_capture)
        file_handler.setFormatter(logging.Formatter('FILE: %(message)s'))
        logger.addHandler(file_handler)
        
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        
        # Both handlers should receive the message
        assert "CONSOLE: Test message" in console_capture.getvalue()
        assert "FILE: Test message" in file_capture.getvalue()


class TestLoggingIntegration:
    """Test logging integration with application components."""
    
    def test_service_logging(self):
        """Test logging integration with service components."""
        from src.core.logging import get_logger
        
        # Test that services can get loggers
        service_logger = get_logger('services.news')
        assert service_logger.name == 'services.news'
        
        repository_logger = get_logger('repositories.article')
        assert repository_logger.name == 'repositories.article'
        
        api_logger = get_logger('api.routes.news')
        assert api_logger.name == 'api.routes.news'
    
    def test_performance_logging(self):
        """Test performance-related logging."""
        import time
        
        log_capture = io.StringIO()
        logger = get_logger('test.performance')
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Simulate timed operation
        start_time = time.time()
        time.sleep(0.01)  # 10ms
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Operation completed in {duration:.3f} seconds")
        
        output = log_capture.getvalue()
        assert "Operation completed in" in output
        assert "seconds" in output
    
    def test_error_correlation(self):
        """Test error correlation and tracking."""
        log_capture = io.StringIO()
        logger = get_logger('test.correlation')
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        # Simulate error with correlation ID
        correlation_id = "corr_12345"
        user_id = "user_67890"
        
        logger.error(
            f"Database connection failed - CorrelationID: {correlation_id}, UserID: {user_id}"
        )
        
        output = log_capture.getvalue()
        assert correlation_id in output
        assert user_id in output
        assert "Database connection failed" in output
    
    def test_sensitive_data_filtering(self):
        """Test filtering of sensitive data from logs."""
        log_capture = io.StringIO()
        logger = get_logger('test.security')
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # This would typically be handled by a custom filter
        # For now, just test that we can log without exposing sensitive data
        api_key = "sk-1234567890abcdef"
        safe_api_key = api_key[:7] + "..." + api_key[-4:]
        
        logger.info(f"API request made with key: {safe_api_key}")
        
        output = log_capture.getvalue()
        assert "sk-1234" in output
        assert "cdef" in output
        assert "567890ab" not in output  # Middle part should be hidden


class TestLoggingConfiguration:
    """Test various logging configuration scenarios."""
    
    @pytest.mark.parametrize("log_level,expected_level", [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
    ])
    def test_log_level_configuration(self, log_level, expected_level):
        """Test different log level configurations."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'development'
            mock_settings.debug = True
            mock_settings.log_level = log_level
            mock_settings.log_format = '%(message)s'
            
            setup_logging()
            
            logger = logging.getLogger()
            assert logger.level == expected_level
    
    def test_invalid_log_level_defaults_to_info(self):
        """Test that invalid log level defaults to INFO."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'development'
            mock_settings.debug = True
            mock_settings.log_level = 'INVALID_LEVEL'
            mock_settings.log_format = '%(message)s'
            
            setup_logging()
            
            logger = logging.getLogger()
            # Should default to INFO when invalid level is provided
            assert logger.level == logging.INFO
    
    def test_custom_log_format(self):
        """Test custom log format configuration."""
        custom_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'development'
            mock_settings.debug = True
            mock_settings.log_level = 'INFO'
            mock_settings.log_format = custom_format
            
            setup_logging()
            
            # Should not raise any errors
            logger = get_logger('test')
            logger.info("Test message")
    
    def test_logging_with_rotating_file_handler(self):
        """Test logging with rotating file handler configuration."""
        with patch('src.core.logging.settings') as mock_settings:
            mock_settings.environment = 'production'
            mock_settings.debug = False
            mock_settings.log_level = 'INFO'
            mock_settings.log_format = '%(message)s'
            mock_settings.log_file = 'app.log'
            mock_settings.log_max_bytes = 1024 * 1024  # 1MB
            mock_settings.log_backup_count = 5
            
            with patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler:
                setup_logging()
                
                # Verify rotating file handler was configured
                mock_rotating_handler.assert_called_once_with(
                    'app.log',
                    maxBytes=1024 * 1024,
                    backupCount=5
                )
