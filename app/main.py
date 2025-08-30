from fastapi import FastAPI
from app.api.routers import tickets, users

app = FastAPI(
    title="Local IT Support AI Agent API",
    description="A FastAPI backend for IT helpdesk workflow management",
    version="1.0.0"
)

# Include routers
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "Local IT Support AI Agent API is running"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Initialize database when running the app directly (not in tests)
if __name__ == "__main__":
    from app.db.init_db import init_database
    init_database()
