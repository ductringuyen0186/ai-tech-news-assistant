#!/usr/bin/env python3
"""
Test Automation Framework Runner
=================================

Comprehensive test runner with multiple modes and reporting.

Usage:
    # Run all tests
    python run_tests.py

    # Run specific test categories
    python run_tests.py --unit
    python run_tests.py --integration
    python run_tests.py --e2e

    # Run with coverage
    python run_tests.py --coverage

    # Run smoke tests only (quick)
    python run_tests.py --smoke

    # Run with detailed output
    python run_tests.py --verbose

    # Skip slow tests
    python run_tests.py --skip-slow

    # CI mode (skip tests requiring external services)
    python run_tests.py --ci

    # Generate HTML report
    python run_tests.py --html-report
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Automated test runner with multiple modes."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize test runner."""
        self.base_dir = base_dir or Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0.0,
            "coverage": None
        }

    def print_header(self, message: str):
        """Print formatted header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message:^70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

    def print_success(self, message: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

    def print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

    def print_warning(self, message: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

    def print_info(self, message: str):
        """Print info message."""
        print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

    def build_pytest_command(self, args: argparse.Namespace) -> List[str]:
        """Build pytest command based on arguments."""
        cmd = ["python", "-m", "pytest"]

        # Test selection
        if args.unit:
            cmd.extend(["-m", "unit"])
        elif args.integration:
            cmd.extend(["-m", "integration"])
        elif args.e2e:
            cmd.extend(["-m", "e2e"])
        elif args.smoke:
            cmd.extend(["-m", "smoke"])

        # Test files
        if args.files:
            cmd.extend(args.files)

        # Verbosity
        if args.verbose:
            cmd.append("-vv")
        elif args.quiet:
            cmd.append("-q")

        # Coverage
        if args.coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ])

        # Performance
        if args.skip_slow:
            cmd.extend(["-m", "not slow"])

        if args.durations:
            cmd.append(f"--durations={args.durations}")

        # CI mode
        if args.ci:
            cmd.extend([
                "-m", "not requires_ollama and not requires_network",
                "--tb=short"
            ])

        # HTML report
        if args.html_report:
            cmd.extend([
                "--html=test_report.html",
                "--self-contained-html"
            ])

        # Parallel execution
        if args.parallel:
            cmd.extend(["-n", str(args.parallel)])

        # Stop on first failure
        if args.exitfirst:
            cmd.append("-x")

        # Show local variables
        if args.showlocals:
            cmd.append("-l")

        # Warnings
        if args.strict_warnings:
            cmd.append("--strict-warnings")

        return cmd

    def run_tests(self, args: argparse.Namespace) -> int:
        """Run tests with specified configuration."""
        self.print_header("🚀 AI Tech News Assistant - Test Automation Framework")

        # Print configuration
        self.print_info(f"Test Directory: {self.base_dir}")
        self.print_info(f"Python: {sys.version.split()[0]}")
        self.print_info(f"Working Directory: {os.getcwd()}")

        # Build command
        cmd = self.build_pytest_command(args)
        
        self.print_info(f"Command: {' '.join(cmd)}")
        print()

        # Run tests
        start_time = datetime.now()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=False,
                text=True
            )
            exit_code = result.returncode
        except Exception as e:
            self.print_error(f"Failed to run tests: {e}")
            return 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        print()
        self.print_header("📊 Test Summary")
        
        if exit_code == 0:
            self.print_success("All tests passed! ✨")
        else:
            self.print_error(f"Some tests failed (exit code: {exit_code})")

        self.print_info(f"Duration: {duration:.2f}s")

        # Coverage report
        if args.coverage:
            print()
            self.print_info("Coverage report generated:")
            self.print_info(f"  - HTML: {self.base_dir / 'htmlcov' / 'index.html'}")
            self.print_info(f"  - XML: {self.base_dir / 'coverage.xml'}")

        # HTML report
        if args.html_report:
            print()
            self.print_info(f"HTML report: {self.base_dir / 'test_report.html'}")

        # Save results
        if args.save_results:
            self.save_results(exit_code, duration, args)

        return exit_code

    def save_results(self, exit_code: int, duration: float, args: argparse.Namespace):
        """Save test results to JSON file."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "duration": duration,
            "passed": exit_code == 0,
            "configuration": {
                "unit": args.unit,
                "integration": args.integration,
                "e2e": args.e2e,
                "smoke": args.smoke,
                "coverage": args.coverage,
                "ci": args.ci
            }
        }

        results_file = self.base_dir / "test_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        self.print_info(f"Results saved to: {results_file}")

    def run_linting(self) -> int:
        """Run code linting with ruff."""
        self.print_header("🔍 Running Code Quality Checks")

        # Ruff check
        self.print_info("Running Ruff linter...")
        result = subprocess.run(
            ["ruff", "check", ".", "--select", "F,E", "--extend-exclude", "test_ollama_integration.py"],
            cwd=self.base_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            self.print_success("Code quality checks passed!")
        else:
            self.print_error("Code quality issues found:")
            print(result.stdout)
            print(result.stderr)

        return result.returncode

    def run_type_checking(self) -> int:
        """Run type checking with mypy."""
        self.print_header("🔍 Running Type Checks")

        self.print_info("Running mypy...")
        result = subprocess.run(
            ["mypy", ".", "--ignore-missing-imports"],
            cwd=self.base_dir,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            self.print_success("Type checks passed!")
        else:
            self.print_warning("Type checking issues found:")
            print(result.stdout)

        return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Automation Framework for AI Tech News Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Test selection
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument(
        "--unit", "-u",
        action="store_true",
        help="Run unit tests only"
    )
    test_group.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Run integration tests only"
    )
    test_group.add_argument(
        "--e2e", "-e",
        action="store_true",
        help="Run end-to-end tests only"
    )
    test_group.add_argument(
        "--smoke", "-s",
        action="store_true",
        help="Run smoke tests only (quick validation)"
    )
    test_group.add_argument(
        "files",
        nargs="*",
        help="Specific test files to run"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    output_group.add_argument(
        "--showlocals", "-l",
        action="store_true",
        help="Show local variables in tracebacks"
    )

    # Coverage
    coverage_group = parser.add_argument_group("Coverage Options")
    coverage_group.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run with coverage reporting"
    )

    # Performance
    perf_group = parser.add_argument_group("Performance Options")
    perf_group.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip slow tests"
    )
    perf_group.add_argument(
        "--durations",
        type=int,
        default=10,
        help="Show N slowest tests (default: 10)"
    )
    perf_group.add_argument(
        "--parallel", "-n",
        type=int,
        metavar="N",
        help="Run tests in parallel with N workers"
    )

    # CI/CD options
    ci_group = parser.add_argument_group("CI/CD Options")
    ci_group.add_argument(
        "--ci",
        action="store_true",
        help="CI mode (skip tests requiring external services)"
    )
    ci_group.add_argument(
        "--exitfirst", "-x",
        action="store_true",
        help="Exit on first failure"
    )
    ci_group.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as errors"
    )

    # Reporting
    report_group = parser.add_argument_group("Reporting Options")
    report_group.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    report_group.add_argument(
        "--save-results",
        action="store_true",
        help="Save test results to JSON file"
    )

    # Quality checks
    quality_group = parser.add_argument_group("Quality Checks")
    quality_group.add_argument(
        "--lint",
        action="store_true",
        help="Run linting checks only"
    )
    quality_group.add_argument(
        "--type-check",
        action="store_true",
        help="Run type checking only"
    )
    quality_group.add_argument(
        "--all-checks",
        action="store_true",
        help="Run all quality checks (lint, type check, tests)"
    )

    args = parser.parse_args()

    # Create runner
    runner = TestRunner()

    # Run requested checks
    exit_codes = []

    if args.lint or args.all_checks:
        exit_codes.append(runner.run_linting())

    if args.type_check or args.all_checks:
        exit_codes.append(runner.run_type_checking())

    if not args.lint and not args.type_check or args.all_checks:
        exit_codes.append(runner.run_tests(args))

    # Return overall exit code
    return max(exit_codes) if exit_codes else 0


if __name__ == "__main__":
    sys.exit(main())
