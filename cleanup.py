#!/usr/bin/env python3
"""
Cleanup Script for AI Tech News Assistant
=========================================

This script removes temporary debugging and test files from both the root directory
and backend directory to keep the repository clean and organized.
"""

import os
import sys
import shutil
from pathlib import Path

def cleanup_directory():
    """Remove temporary debugging and test files from the root and backend directories."""
    
    # Get the root directory
    root_dir = Path(__file__).parent
    backend_dir = root_dir / "backend"
    
    print("🧹 Cleaning up temporary files...")
    print(f"📁 Working in: {root_dir}")
    print()
    
    # Root directory files to remove (debugging and test scripts that should not be in root)
    root_files_to_remove = [
        'debug_conversion.py',
        'debug_import.py', 
        'test_article_direct.py',
        'test_article_model.py',
        'test_debug_repo.py',
        'test_direct_import.py',
        'test_manual_conversion.py',
        'test_repo_method.py'
    ]
    
    # Backend directory files to remove (old debugging and temporary files)
    backend_files_to_remove = [
        'article_repository_backup.py',
        'check_get_by_id.py',
        'check_method.py', 
        'create_article_repo.py',
        'force_reload.py',
        'run.py',
        'test_exact_scenario.py',
        'test_content_parser.py',
        'test_embeddings.py',
        'test_rss.py',
        'test_summarization.py',
        'test_api.bat',
        'test_api.ps1',
        'setup_python.bat',
        'main.py',  # Old main.py, we have src/main.py now
        'manage_embeddings.py'  # Old utility, should be in scripts if needed
    ]
    
    # Backend directories to remove (old structure)
    backend_dirs_to_remove = [
        'api',           # Old API structure, replaced by src/api
        'ingestion',     # Old ingestion, replaced by src/services
        'llm',           # Old LLM, replaced by src/services
        'rag',           # Old RAG, replaced by src/services
        'utils',         # Old utils, replaced by src/core
        'vectorstore'    # Old vectorstore, replaced by src/repositories
    ]
    
    # Files to keep in backend
    backend_files_to_keep = [
        'src/',
        'tests/',
        'scripts/',
        'requirements.txt',
        '.env.example', 
        'data/',
        'venv/',
        '.coverage',
        'htmlcov/',
        '.pytest_cache/',
        'REFACTORING_COMPLETE.md',
        'LLM_SUMMARIZATION.md'
    ]
    
    removed_count = 0
    
    # Clean root directory
    print("🗂️ Cleaning root directory...")
    for file_name in root_files_to_remove:
        file_path = root_dir / file_name
        
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    print(f"✅ Removed: {file_name}")
                    removed_count += 1
                else:
                    print(f"⚠️  Skipped: {file_name} (not a file)")
            except Exception as e:
                print(f"❌ Failed to remove {file_name}: {e}")
        else:
            print(f"ℹ️  Not found: {file_name}")
    
    # Clean backend directory
    print(f"\n🗂️ Cleaning backend directory...")
    
    # Remove old files
    for file_name in backend_files_to_remove:
        file_path = backend_dir / file_name
        
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    print(f"✅ Removed: backend/{file_name}")
                    removed_count += 1
                else:
                    print(f"⚠️  Skipped: backend/{file_name} (not a file)")
            except Exception as e:
                print(f"❌ Failed to remove backend/{file_name}: {e}")
        else:
            print(f"ℹ️  Not found: backend/{file_name}")
    
    # Remove old directories
    for dir_name in backend_dirs_to_remove:
        dir_path = backend_dir / dir_name
        
        if dir_path.exists():
            try:
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    print(f"📁 Removed directory: backend/{dir_name}/")
                    removed_count += 1
                else:
                    print(f"⚠️  Skipped: backend/{dir_name} (not a directory)")
            except Exception as e:
                print(f"❌ Failed to remove backend/{dir_name}/: {e}")
        else:
            print(f"ℹ️  Not found: backend/{dir_name}/")
    
    print()
    print(f"🎉 Cleanup complete! Removed {removed_count} items.")
    
    # Show what's left in the root directory
    print("\n📋 Remaining files in root directory:")
    for item in sorted(root_dir.iterdir()):
        if item.name.startswith('.'):
            continue  # Skip hidden files/directories
        
        if item.is_dir():
            print(f"  📁 {item.name}/")
        else:
            print(f"  📄 {item.name}")
    
    # Show what's left in the backend directory
    print(f"\n📋 Remaining files in backend directory:")
    for item in sorted(backend_dir.iterdir()):
        if item.name.startswith('.') and item.name not in ['.env.example', '.coverage']:
            continue  # Skip hidden files except important ones
        
        if item.is_dir():
            print(f"  📁 {item.name}/")
        else:
            print(f"  📄 {item.name}")
    
    print("\n✨ Both directories are now clean!")
    print("\n📚 Clean Architecture Summary:")
    print("Root directory: Essential docs and configs only")
    print("Backend directory: Refactored src/ structure with tests/ and configs")

if __name__ == "__main__":
    cleanup_directory()
