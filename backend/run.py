#!/usr/bin/env python3
"""
Run script for the AI Tech News Assistant
"""
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    import uvicorn
    
    try:
        # Import the app
        print("Importing application...")
        from src.main import app
        print("Application imported successfully!")
        
        # Run the server
        print("Starting server on http://127.0.0.1:8001")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,
            reload=False,  # Disable reload to avoid the warning
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
