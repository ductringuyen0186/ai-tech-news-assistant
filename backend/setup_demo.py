#!/usr/bin/env python3
"""
AI/ML Demo Setup Script
=======================

Quick setup script to install and configure everything needed for the AI/ML demo.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and show progress."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("🚀 AI/ML Demo Setup")
    print("=" * 30)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Install core dependencies
    core_deps = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "httpx",
        "feedparser",
        "beautifulsoup4",
        "newspaper3k",
        "python-multipart"
    ]
    
    # Install AI/ML dependencies
    ai_deps = [
        "sentence-transformers",
        "torch",
        "numpy",
        "scikit-learn",
        "chromadb",
        "langchain",
        "transformers"
    ]
    
    # Optional dependencies
    optional_deps = [
        "anthropic",  # Claude API
        "ollama",     # Ollama client
    ]
    
    print("📦 Installing core dependencies...")
    for dep in core_deps:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    print("\n🤖 Installing AI/ML dependencies...")
    for dep in ai_deps:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    print("\n⚙️ Installing optional dependencies...")
    for dep in optional_deps:
        run_command(f"pip install {dep}", f"Installing {dep} (optional)")
    
    # Create necessary directories
    dirs_to_create = [
        "data",
        "data/articles",
        "data/embeddings",
        "data/models",
        "logs"
    ]
    
    print("\n📁 Creating directories...")
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"✅ Created {dir_path}")
    
    # Create basic .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("\n🔧 Creating .env configuration...")
        env_content = """# AI Tech News Assistant Configuration
DATABASE_URL=sqlite:///./data/news.db
ANTHROPIC_API_KEY=your_claude_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=all-MiniLM-L6-v2
LOG_LEVEL=INFO
"""
        env_file.write_text(env_content)
        print("✅ Created .env file")
    
    # Download a small embedding model for demo
    print("\n🔮 Downloading embedding model for demo...")
    try:
        import sentence_transformers
        model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model ready")
    except Exception as e:
        print(f"⚠️ Could not pre-download model: {e}")
    
    print("\n🎯 Setup Complete!")
    print("\nNext steps:")
    print("1. Install Ollama (optional): https://ollama.ai/download")
    print("2. Pull a model: ollama pull llama2")
    print("3. Get Claude API key (optional): https://console.anthropic.com/")
    print("4. Run the demo: python demo_ai_ml.py")

if __name__ == "__main__":
    main()
