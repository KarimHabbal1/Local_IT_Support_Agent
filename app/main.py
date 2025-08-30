from fastapi import FastAPI
from app.api.routers import tickets, users

app = FastAPI(title="Local IT Support AI Agent API", version="1.0")

app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
