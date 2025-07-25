#!/usr/bin/env python3
"""
Configuration Validation Script for AI Tech News Assistant

This script validates the environment configuration and checks for common issues.
Run this script after setting up your .env file to ensure everything is configured correctly.

Usage:
    python validate_config.py
    python validate_config.py --env production
    python validate_config.py --check-services
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import requests
from urllib.parse import urlparse

# Add src to path to import our config
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.config import Settings, Environment, LLMProvider, DatabaseType
except ImportError as e:
    print(f"❌ Failed to import configuration: {e}")
    print("Make sure you're running this script from the backend directory")
    sys.exit(1)


class ConfigValidator:
    """Validates environment configuration and external services."""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.settings: Optional[Settings] = None
        
    def load_config(self) -> bool:
        """Load and validate the configuration."""
        try:
            if self.env_file:
                os.environ["ENV_FILE"] = self.env_file
            
            self.settings = Settings()
            print(f"✅ Configuration loaded successfully")
            print(f"   Environment: {self.settings.environment}")
            print(f"   Debug mode: {self.settings.debug}")
            print(f"   Database type: {self.settings.database_type}")
            print(f"   LLM provider: {self.settings.default_llm_provider}")
            return True
            
        except Exception as e:
            self.issues.append(f"Failed to load configuration: {e}")
            return False
    
    def validate_environment(self) -> None:
        """Validate environment-specific settings."""
        if not self.settings:
            return
            
        # Production-specific validations
        if self.settings.environment == Environment.PRODUCTION:
            if self.settings.debug:
                self.issues.append("Debug mode is enabled in production")
            
            if self.settings.secret_key.get_secret_value() == "your-super-secret-key-change-this-in-production-at-least-32-chars":
                self.issues.append("Default secret key is being used in production")
            
            if "*" in self.settings.allowed_origins:
                self.issues.append("Wildcard CORS origins not allowed in production")
            
            if self.settings.error_detail_in_response:
                self.warnings.append("Error details in response enabled in production")
        
        # Development-specific validations
        if self.settings.environment == Environment.DEVELOPMENT:
            if not self.settings.debug:
                self.warnings.append("Debug mode is disabled in development")
        
        # Secret key validation
        secret_len = len(self.settings.secret_key.get_secret_value())
        if secret_len < 32:
            self.issues.append(f"Secret key is too short ({secret_len} chars, minimum 32)")
    
    def validate_database(self) -> None:
        """Validate database configuration."""
        if not self.settings:
            return
            
        if self.settings.database_type == DatabaseType.SQLITE:
            db_path = Path(self.settings.sqlite_database_path)
            if not db_path.parent.exists():
                self.warnings.append(f"SQLite database directory does not exist: {db_path.parent}")
        
        elif self.settings.database_type in [DatabaseType.POSTGRESQL, DatabaseType.MYSQL]:
            if not self.settings.database_url:
                self.issues.append(f"Database URL required for {self.settings.database_type}")
            else:
                try:
                    parsed = urlparse(self.settings.database_url)
                    if not all([parsed.scheme, parsed.hostname]):
                        self.issues.append("Invalid database URL format")
                except Exception as e:
                    self.issues.append(f"Failed to parse database URL: {e}")
    
    def validate_llm_config(self) -> None:
        """Validate LLM provider configuration."""
        if not self.settings:
            return
            
        provider = self.settings.default_llm_provider
        
        if provider == LLMProvider.OPENAI:
            if not self.settings.openai_api_key:
                self.issues.append("OpenAI API key is required when using OpenAI provider")
            else:
                key = self.settings.openai_api_key.get_secret_value()
                if key.startswith("your-") or key == "":
                    self.issues.append("Invalid OpenAI API key")
        
        elif provider == LLMProvider.ANTHROPIC:
            if not self.settings.anthropic_api_key:
                self.issues.append("Anthropic API key is required when using Anthropic provider")
            else:
                key = self.settings.anthropic_api_key.get_secret_value()
                if key.startswith("your-") or key == "":
                    self.issues.append("Invalid Anthropic API key")
        
        elif provider == LLMProvider.HUGGINGFACE:
            if not self.settings.huggingface_api_key:
                self.warnings.append("HuggingFace API key not set - some models may not work")
        
        elif provider == LLMProvider.OLLAMA:
            if not self.settings.ollama_host.startswith(("http://", "https://")):
                self.issues.append("Invalid Ollama host URL")
    
    def validate_directories(self) -> None:
        """Validate required directories exist or can be created."""
        if not self.settings:
            return
            
        directories = [
            ("ChromaDB persist directory", Path(self.settings.chroma_persist_directory)),
        ]
        
        if self.settings.log_file:
            directories.append(("Log file directory", Path(self.settings.log_file).parent))
        
        for name, path in directories:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ {name}: {path}")
            except Exception as e:
                self.issues.append(f"Cannot create {name} at {path}: {e}")
    
    def check_external_services(self) -> None:
        """Check connectivity to external services."""
        if not self.settings:
            return
            
        print("\n🔍 Checking external service connectivity...")
        
        # Check Ollama if it's the default provider
        if self.settings.default_llm_provider == LLMProvider.OLLAMA:
            try:
                response = requests.get(
                    f"{self.settings.ollama_host}/api/tags",
                    timeout=5
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    print(f"✅ Ollama service accessible ({len(models)} models available)")
                    
                    # Check if the configured model is available
                    model_names = [model.get("name", "").split(":")[0] for model in models]
                    if self.settings.ollama_model.split(":")[0] not in model_names:
                        self.warnings.append(f"Configured Ollama model '{self.settings.ollama_model}' not found")
                else:
                    self.warnings.append(f"Ollama service returned status {response.status_code}")
            except requests.RequestException as e:
                self.warnings.append(f"Cannot connect to Ollama at {self.settings.ollama_host}: {e}")
        
        # Check RSS feeds (sample a few)
        print("📰 Checking RSS feed accessibility...")
        for source in self.settings.rss_sources[:3]:  # Check first 3 sources
            try:
                response = requests.head(
                    source["url"],
                    timeout=self.settings.rss_timeout,
                    headers={"User-Agent": "AI-Tech-News-Assistant/1.0"}
                )
                if response.status_code == 200:
                    print(f"✅ RSS feed accessible: {source['name']}")
                else:
                    self.warnings.append(f"RSS feed {source['name']} returned status {response.status_code}")
            except requests.RequestException as e:
                self.warnings.append(f"Cannot access RSS feed {source['name']}: {e}")
    
    def generate_report(self) -> None:
        """Generate and display validation report."""
        print("\n" + "="*80)
        print("🔍 CONFIGURATION VALIDATION REPORT")
        print("="*80)
        
        if self.issues:
            print(f"\n❌ ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        if not self.issues and not self.warnings:
            print("\n✅ All validations passed! Configuration looks good.")
        elif not self.issues:
            print("\n✅ No critical issues found. Please review warnings.")
        else:
            print(f"\n❌ Found {len(self.issues)} critical issues that need to be fixed.")
        
        print("\n" + "="*80)
    
    def run_validation(self, check_services: bool = False) -> bool:
        """Run all validation checks."""
        print("🔍 Validating AI Tech News Assistant configuration...")
        
        if not self.load_config():
            self.generate_report()
            return False
        
        print("\n📋 Running configuration validations...")
        self.validate_environment()
        self.validate_database()
        self.validate_llm_config()
        self.validate_directories()
        
        if check_services:
            self.check_external_services()
        
        self.generate_report()
        
        return len(self.issues) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate AI Tech News Assistant configuration"
    )
    parser.add_argument(
        "--env",
        help="Environment file to use (e.g., .env.production)",
        default=None
    )
    parser.add_argument(
        "--check-services",
        action="store_true",
        help="Check connectivity to external services"
    )
    
    args = parser.parse_args()
    
    # Change to backend directory if not already there
    backend_dir = Path(__file__).parent
    if backend_dir.name == "backend":
        os.chdir(backend_dir)
    
    validator = ConfigValidator(args.env)
    success = validator.run_validation(args.check_services)
    
    if not success:
        print("\n💡 Tips:")
        print("   - Copy .env.example to .env and configure your settings")
        print("   - Check the documentation for configuration details")
        print("   - Run with --check-services to test external connectivity")
        sys.exit(1)
    
    print("\n🚀 Configuration is valid! You're ready to run the application.")


if __name__ == "__main__":
    main()
