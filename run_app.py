import os
import sys
import uvicorn

# Ensure backend package is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.database import init_db

if __name__ == "__main__":
    print("=" * 70)
    print(" ADAPTIVE LEAST-PRIVILEGE TOOL SCOPING PLATFORM")
    print(" Model-Scale Evaluation Framework (3B vs 70B)")
    print("=" * 70)
    
    print("\n[1/2] Initializing SQLite database and baseline experimental benchmarks...")
    init_db()
    
    print("[2/2] Starting Web Server on http://localhost:8000 ...")
    print("      - Frontend SPA: http://localhost:8000/")
    print("      - Interactive OpenAPI Docs: http://localhost:8000/docs\n")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
