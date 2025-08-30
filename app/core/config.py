"""
Configuration settings for the Local IT Support Agent
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    app_name: str = "Local IT Support AI Agent"
    version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "sqlite:///./support_agent.db"
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    
    # Pagination defaults
    default_page_size: int = 50
    max_page_size: int = 100
    
    class Config:
        env_file = ".env"

settings = Settings()
