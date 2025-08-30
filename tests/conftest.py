import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.models import Base
from app.db.session import get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_client():
    # Create tables for each test
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as client:
        yield client
    
    # Clean up after each test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_users(test_client):
    """Create test users"""
    user1 = test_client.post("/api/v1/users/", json={"username": "alice"})
    user2 = test_client.post("/api/v1/users/", json={"username": "bob"})
    return user1.json(), user2.json()
