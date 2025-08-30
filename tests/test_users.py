import pytest

class TestUsers:
    
    def test_create_user(self, test_client):
        """Test creating a user"""
        response = test_client.post(
            "/api/v1/users/",
            json={"username": "alice"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "alice"
        assert "id" in data
    
    def test_create_user_duplicate_username(self, test_client):
        """Test creating a user with duplicate username"""
        # Create first user
        test_client.post("/api/v1/users/", json={"username": "alice"})
        
        # Try to create another with same username
        response = test_client.post(
            "/api/v1/users/",
            json={"username": "alice"}
        )
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    def test_create_user_invalid_data(self, test_client):
        """Test creating a user with invalid data"""
        response = test_client.post(
            "/api/v1/users/",
            json={"username": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_list_users(self, test_client):
        """Test listing users"""
        # Create some users
        test_client.post("/api/v1/users/", json={"username": "alice"})
        test_client.post("/api/v1/users/", json={"username": "bob"})
        test_client.post("/api/v1/users/", json={"username": "charlie"})
        
        response = test_client.get("/api/v1/users/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["users"]) == 3
        usernames = [user["username"] for user in data["users"]]
        assert "alice" in usernames
        assert "bob" in usernames
        assert "charlie" in usernames
    
    def test_list_users_empty(self, test_client):
        """Test listing users when none exist"""
        response = test_client.get("/api/v1/users/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["users"]) == 0
    
    def test_get_user_by_id(self, test_client):
        """Test getting a user by ID"""
        # Create user
        create_response = test_client.post(
            "/api/v1/users/",
            json={"username": "alice"}
        )
        user_id = create_response.json()["id"]
        
        # Get user
        response = test_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "alice"
    
    def test_get_user_not_found(self, test_client):
        """Test getting a user that doesn't exist"""
        response = test_client.get("/api/v1/users/999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
