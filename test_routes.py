import sys
sys.path.insert(0, 'c:/Users/Tri/OneDrive/Desktop/Portfolio/ai-tech-news-assistant/backend')

try:
    from src.api.routes import api_router, root_router
    print(f" Routes loaded: {len(api_router.routes)} API routes, {len(root_router.routes)} root routes")
    
    # List all RAG routes
    rag_routes = [r for r in api_router.routes if '/rag' in str(r.path)]
    print(f" RAG routes found: {len(rag_routes)}")
    for route in rag_routes:
        print(f"  - {route.methods} {route.path}")
    
    print("\n All tests passed! Ready to start server.")
except Exception as e:
    print(f" Error: {e}")
    import traceback
    traceback.print_exc()
