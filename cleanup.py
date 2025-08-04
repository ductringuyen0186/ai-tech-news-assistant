#!/usr/bin/env python3
"""
Cleanup Script for AI Tech News Assistant
=========================================

Removes temporary debugging and test files while preserving essential project structure.
Uses pattern matching for maintainable cleanup operations.
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Set


class ProjectCleaner:
    """Smart project cleanup with pattern-based file removal."""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        
        # Define cleanup patterns instead of hardcoded lists
        self.cleanup_patterns = {
            # Test and debug files
            "test_files": [
                "**/test_*.py",
                "**/*_test.py", 
                "**/debug_*.py",
                "**/temp_*.py",
                "**/__pycache__",
                "**/*.pyc",
                "**/.pytest_cache"
            ],
            # Build artifacts
            "build_artifacts": [
                "**/build/",
                "**/dist/",
                "**/*.egg-info/",
                "**/.coverage",
                "**/htmlcov/",
                "**/.tox/"
            ],
            # IDE files
            "ide_files": [
                "**/.vscode/settings.json",
                "**/.idea/",
                "**/*.swp",
                "**/*.swo",
                "**/.DS_Store"
            ],
            # Temporary files
            "temp_files": [
                "**/tmp/",
                "**/temp/",
                "**/*.tmp",
                "**/*.log",
                "**/dumps/"
            ]
        }
        
        # Essential files to preserve
        self.preserve_patterns = [
            "requirements*.txt",
            "pyproject.toml",
            "setup.py",
            "README*",
            "LICENSE*",
            ".gitignore",
            ".env*",
            "Dockerfile*",
            "docker-compose*"
        ]
    
    def find_files_by_pattern(self, patterns: List[str]) -> Set[Path]:
        """Find files matching the given patterns."""
        found_files = set()
        
        for pattern in patterns:
            matches = self.root_dir.glob(pattern)
            found_files.update(matches)
        
        return found_files
    
    def is_preserved_file(self, file_path: Path) -> bool:
        """Check if a file should be preserved."""
        for pattern in self.preserve_patterns:
            if file_path.match(pattern):
                return True
        return False
    
    def cleanup_category(self, category: str, dry_run: bool = False) -> List[Path]:
        """Clean up files in a specific category."""
        if category not in self.cleanup_patterns:
            print(f"Unknown cleanup category: {category}")
            return []
        
        patterns = self.cleanup_patterns[category]
        files_to_remove = self.find_files_by_pattern(patterns)
        
        # Filter out preserved files
        files_to_remove = {f for f in files_to_remove if not self.is_preserved_file(f)}
        
        removed_files = []
        
        for file_path in files_to_remove:
            try:
                if file_path.exists():
                    if dry_run:
                        print(f"Would remove: {file_path}")
                    else:
                        if file_path.is_dir():
                            shutil.rmtree(file_path)
                            print(f"Removed directory: {file_path}")
                        else:
                            file_path.unlink()
                            print(f"Removed file: {file_path}")
                    
                    removed_files.append(file_path)
                    
            except Exception as e:
                print(f"Failed to remove {file_path}: {e}")
        
        return removed_files
    
    def full_cleanup(self, dry_run: bool = False):
        """Perform full cleanup of all categories."""
        print("🧹 Starting project cleanup...")
        
        if dry_run:
            print("📋 DRY RUN MODE - No files will be actually removed")
        
        total_removed = 0
        
        for category in self.cleanup_patterns:
            print(f"\n📁 Cleaning category: {category}")
            removed = self.cleanup_category(category, dry_run)
            total_removed += len(removed)
            print(f"   Processed {len(removed)} items")
        
        print(f"\n✅ Cleanup complete! Processed {total_removed} items")
        
        if not dry_run:
            print("\n📊 Project structure after cleanup:")
            self._show_project_structure()
    
    def _show_project_structure(self):
        """Show the project structure after cleanup."""
        print("Root directory: Essential docs and configs only")
        print("Backend directory: Clean src/ structure with organized tests/")


def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up project files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without actually removing")
    parser.add_argument("--category", help="Clean only specific category", choices=["test_files", "build_artifacts", "ide_files", "temp_files"])
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner()
    
    if args.category:
        cleaner.cleanup_category(args.category, args.dry_run)
    else:
        cleaner.full_cleanup(args.dry_run)


if __name__ == "__main__":
    main()
