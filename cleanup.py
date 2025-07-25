#!/usr/bin/env python3
"""
Cleanup Script for AI Tech News Assistant
=========================================

This script removes temporary debugging and test files from the root directory
to keep the repository clean and organized.
"""

import os
import sys
from pathlib import Path

def cleanup_directory():
    """Remove temporary debugging and test files from the root directory."""
    
    # Get the root directory (parent of backend)
    root_dir = Path(__file__).parent
    
    # Files to remove (debugging and test scripts that should not be in root)
    files_to_remove = [
        'debug_conversion.py',
        'debug_import.py', 
        'test_article_direct.py',
        'test_article_model.py',
        'test_debug_repo.py',
        'test_direct_import.py',
        'test_manual_conversion.py',
        'test_repo_method.py'
    ]
    
    # Files to keep (legitimate documentation and configuration)
    files_to_keep = [
        'QUICK_START.md',  # This looks like legitimate documentation
        'README.md',
        '.gitignore',
        '.github/',
        'backend/',
        '.git/',
        '.copilot/'
    ]
    
    print("🧹 Cleaning up temporary files...")
    print(f"📁 Working in: {root_dir}")
    print()
    
    removed_count = 0
    
    for file_name in files_to_remove:
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
    
    print()
    print(f"🎉 Cleanup complete! Removed {removed_count} files.")
    
    # Show what's left in the directory
    print("\n📋 Remaining files in root directory:")
    for item in sorted(root_dir.iterdir()):
        if item.name.startswith('.'):
            continue  # Skip hidden files/directories
        
        if item.is_dir():
            print(f"  📁 {item.name}/")
        else:
            print(f"  📄 {item.name}")
    
    print("\n✨ Directory is now clean!")

if __name__ == "__main__":
    cleanup_directory()
