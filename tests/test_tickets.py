import pytest

class TestTickets:
    
    def test_create_ticket(self, test_client, test_users):
        """Test creating a ticket"""
        alice, bob = test_users
        
        response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["issue"] == "VPN not working"
        assert data["status"] == "NEW"
        assert data["assigned_to"] == alice["id"]
        assert len(data["logs"]) == 1
        assert data["logs"][0]["action"] == "ticket_created"
    
    def test_create_ticket_without_assignment(self, test_client):
        """Test creating a ticket without assignment"""
        response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "Printer not working"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["issue"] == "Printer not working"
        assert data["assigned_to"] is None
    
    def test_create_ticket_invalid_user(self, test_client):
        """Test creating a ticket with invalid assigned user"""
        response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": 999}
        )
        
        assert response.status_code == 400
        assert "Assigned user does not exist" in response.json()["detail"]
    
    def test_get_ticket(self, test_client, test_users):
        """Test getting a ticket by ID"""
        alice, _ = test_users
        
        # Create ticket
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        # Get ticket
        response = test_client.get(f"/api/v1/tickets/{ticket_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert data["issue"] == "VPN not working"
    
    def test_get_nonexistent_ticket(self, test_client):
        """Test getting a nonexistent ticket"""
        response = test_client.get("/api/v1/tickets/999")
        assert response.status_code == 404
    
    def test_list_tickets(self, test_client, test_users):
        """Test listing tickets"""
        alice, bob = test_users
        
        # Create multiple tickets
        test_client.post("/api/v1/tickets", json={"issue": "VPN issue", "assigned_to": alice["id"]})
        test_client.post("/api/v1/tickets", json={"issue": "Printer issue", "assigned_to": bob["id"]})
        test_client.post("/api/v1/tickets", json={"issue": "Network issue"})
        
        response = test_client.get("/api/v1/tickets")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["tickets"]) == 3
    
    def test_list_tickets_with_filter(self, test_client, test_users):
        """Test listing tickets with status filter"""
        alice, _ = test_users
        
        # Create and update ticket
        create_response = test_client.post(
            "/api/v1/tickets", 
            json={"issue": "VPN issue", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "IN_PROGRESS"}
        )
        
        # Create another ticket (stays NEW)
        test_client.post("/api/v1/tickets", json={"issue": "Printer issue"})
        
        # Filter by status
        response = test_client.get("/api/v1/tickets?status=IN_PROGRESS")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tickets"][0]["status"] == "IN_PROGRESS"
    
    def test_valid_status_transitions(self, test_client, test_users):
        """Test valid status transitions"""
        alice, _ = test_users
        
        # Create ticket
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        # NEW -> IN_PROGRESS
        response = test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "IN_PROGRESS"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "IN_PROGRESS"
        
        # IN_PROGRESS -> RESOLVED
        response = test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "RESOLVED"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RESOLVED"
        
        # RESOLVED -> IN_PROGRESS (re-open)
        response = test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "IN_PROGRESS"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "IN_PROGRESS"
    
    def test_invalid_status_transitions(self, test_client, test_users):
        """Test invalid status transitions"""
        alice, _ = test_users
        
        # Create ticket
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        # NEW -> RESOLVED (invalid)
        response = test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "RESOLVED"}
        )
        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]
    
    def test_close_ticket_success(self, test_client, test_users):
        """Test closing a resolved ticket"""
        alice, _ = test_users
        
        # Create and progress ticket to RESOLVED
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        test_client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "IN_PROGRESS"})
        test_client.patch(f"/api/v1/tickets/{ticket_id}", json={"status": "RESOLVED"})
        
        # Close ticket
        response = test_client.post(
            f"/api/v1/tickets/{ticket_id}/close",
            json={"resolution_code": "VPN-RESET-OK"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"
        
        # Check logs
        close_log = [log for log in data["logs"] if log["action"] == "ticket_closed"][0]
        assert close_log["details"]["resolution_code"] == "VPN-RESET-OK"
    
    def test_close_ticket_invalid_status(self, test_client, test_users):
        """Test closing a ticket that's not RESOLVED"""
        alice, _ = test_users
        
        # Create ticket (status = NEW)
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        # Try to close
        response = test_client.post(
            f"/api/v1/tickets/{ticket_id}/close",
            json={"resolution_code": "VPN-RESET-OK"}
        )
        
        assert response.status_code == 400
        assert "Can only close tickets with RESOLVED status" in response.json()["detail"]
    
    def test_update_ticket_issue(self, test_client, test_users):
        """Test updating ticket issue"""
        alice, _ = test_users
        
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        response = test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"issue": "VPN connection failed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["issue"] == "VPN connection failed"
        
        # Check update log
        update_logs = [log for log in data["logs"] if log["action"] == "ticket_updated"]
        assert len(update_logs) == 1
        assert "issue" in update_logs[0]["details"]
    
    def test_update_ticket_assignment(self, test_client, test_users):
        """Test updating ticket assignment"""
        alice, bob = test_users
        
        create_response = test_client.post(
            "/api/v1/tickets",
            json={"issue": "VPN not working", "assigned_to": alice["id"]}
        )
        ticket_id = create_response.json()["id"]
        
        response = test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"assigned_to": bob["id"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == bob["id"]
