#!/usr/bin/env python3
"""
Run the FastAPI application using Uvicorn.
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Configure Uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "true").lower() == "true",
        workers=int(os.getenv("WORKERS", 1)),
    )
