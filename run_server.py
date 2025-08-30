#!/usr/bin/env python3
"""
Startup script for the Local IT Support Agent API
"""
import sys
import uvicorn

if __name__ == "__main__":
    # Initialize database first
    from app.db.init_db import init_database
    print("Initializing database...")
    init_database()
    
    # Start the server
    print("Starting Local IT Support Agent API...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("API Health Check: http://localhost:8000/health")
    print("Press CTRL+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
