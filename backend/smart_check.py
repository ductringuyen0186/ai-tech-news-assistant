#!/usr/bin/env python3
"""
Smart Test Analyzer - No execution, just static analysis!
========================================================
"""
from pathlib import Path

def analyze_file_imports(file_path):
    """Check if file can be imported (basic syntax check)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic syntax validation
        compile(content, file_path, 'exec')
        return True, "✓ Syntax OK"
    except SyntaxError as e:
        return False, f"❌ Syntax Error: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

def check_model_structure():
    """Check if models have required fields"""
    models_file = Path("src/models/article.py")
    if not models_file.exists():
        return False, "❌ article.py not found"
    
    with open(models_file, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check ArticleSummary has required fields
    if 'class ArticleSummary' in content:
        required_fields = ['id:', 'title:', 'source:']
        missing = [field for field in required_fields if field not in content]
        if missing:
            issues.append(f"ArticleSummary missing: {missing}")
    
    # Check AISummary exists
    if 'class AISummary' not in content:
        issues.append("AISummary class not found")
    
    if issues:
        return False, f"❌ Model issues: {'; '.join(issues)}"
    
    return True, "✓ Models structure OK"

def check_service_attributes():
    """Check if NewsService has required attributes"""
    service_file = Path("src/services/news_service.py")
    if not service_file.exists():
        return False, "❌ news_service.py not found"
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    required_attrs = [
        'self.article_min_length',
        'self.max_articles_per_feed'
    ]
    
    missing = [attr for attr in required_attrs if attr not in content]
    
    if missing:
        return False, f"❌ NewsService missing: {missing}"
    
    return True, "✓ NewsService attributes OK"

def check_health_routes():
    """Check health routes structure"""
    health_file = Path("src/api/routes/health.py")
    if not health_file.exists():
        return False, "❌ health.py not found"
    
    with open(health_file, 'r') as f:
        content = f.read()
    
    required_routes = [
        '@router.get("/health")',
        '@router.get("/readiness")',
        '@router.get("/liveness")',
        '@router.get("/metrics")'
    ]
    
    missing = [route for route in required_routes if route not in content]
    
    if missing:
        return False, f"❌ Missing routes: {missing}"
    
    return True, "✓ Health routes OK"

def main():
    """Run smart static analysis"""
    print("🔍 Smart Static Analysis - Instant Results!")
    print("=" * 50)
    
    checks = [
        ("Model Structure", check_model_structure),
        ("Service Attributes", check_service_attributes),
        ("Health Routes", check_health_routes),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        success, message = check_func()
        print(f"   {message}")
        if success:
            passed += 1
    
    print(f"\n📊 Static Analysis Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All components structurally sound!")
        print("\n💡 Next: Run individual tests:")
        print("   py -m pytest backend/tests/unit/test_models.py -v")
        print("   py -m pytest backend/tests/unit/test_health_routes.py::TestHealthRoutes::test_health_check_response_structure -v")
    else:
        print("⚠️  Issues found - check the details above")
    
    return passed == total

if __name__ == "__main__":
    main()
