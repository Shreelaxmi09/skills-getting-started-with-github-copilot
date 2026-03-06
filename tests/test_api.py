"""
Tests for the FastAPI High School Management System API

Tests covering:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- DELETE /activities/{activity_name}/signup endpoint
- Error handling for non-existent activities and participants
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_initial_dictionary(self):
        """Test that GET /activities returns the initial dictionary with Chess Club, Programming Class, and Gym Class"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify the required keys are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify structure of returned data
        assert isinstance(data["Chess Club"], dict)
        assert isinstance(data["Programming Class"], dict)
        assert isinstance(data["Gym Class"], dict)
        
        # Verify initial participants for each activity
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
        assert data["Programming Class"]["participants"] == ["emma@mergington.edu", "sophia@mergington.edu"]
        assert data["Gym Class"]["participants"] == ["john@mergington.edu", "olivia@mergington.edu"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successfully signing up a new email to an activity"""
        # Reset the activity state to remove the test user if they exist
        test_email = "testuser@mergington.edu"
        if test_email in activities["Chess Club"]["participants"]:
            activities["Chess Club"]["participants"].remove(test_email)
        
        initial_count = len(activities["Chess Club"]["participants"])
        
        # Sign up for an activity
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": test_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response message
        assert "message" in data
        assert data["message"] == f"Signed up {test_email} for Chess Club"
        
        # Verify the email was added to the activity
        assert test_email in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1

    def test_signup_for_activity_preserves_existing_participants(self):
        """Test that signup preserves existing participants"""
        test_email = "another_test@mergington.edu"
        if test_email in activities["Programming Class"]["participants"]:
            activities["Programming Class"]["participants"].remove(test_email)
        
        # Capture initial participants
        initial_participants = activities["Programming Class"]["participants"].copy()
        
        # Sign up
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": test_email}
        )
        
        assert response.status_code == 200
        
        # Verify all initial participants are still there
        for participant in initial_participants:
            assert participant in activities["Programming Class"]["participants"]
        
        # Verify new participant was added
        assert test_email in activities["Programming Class"]["participants"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with a duplicate email returns 400"""
        # Use an already existing participant
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Student already signed up"


class TestRemoveParticipant:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint"""

    def test_delete_participant_success(self):
        """Test successfully removing a participant from an activity"""
        # First add a participant
        test_email = "delete_test@mergington.edu"
        if test_email not in activities["Gym Class"]["participants"]:
            activities["Gym Class"]["participants"].append(test_email)
        
        initial_count = len(activities["Gym Class"]["participants"])
        
        # Remove the participant
        response = client.delete(
            "/activities/Gym Class/signup",
            params={"email": test_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response message
        assert "message" in data
        assert data["message"] == f"Removed {test_email} from Gym Class"
        
        # Verify the email was removed from the activity
        assert test_email not in activities["Gym Class"]["participants"]
        assert len(activities["Gym Class"]["participants"]) == initial_count - 1

    def test_delete_participant_preserves_others(self):
        """Test that deleting a participant doesn't affect others"""
        # Use an existing participant we can safely delete
        activity_name = "Basketball Team"
        email_to_delete = "james@mergington.edu"
        test_email = "preserve_test@mergington.edu"
        
        # Add our test email if not there
        if test_email not in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].append(test_email)
        
        initial_participants = activities[activity_name]["participants"].copy()
        
        # Add another test participant to be safe
        other_email = "other_preserve@mergington.edu"
        if other_email not in activities[activity_name]["participants"]:
            activities[activity_name]["participants"].append(other_email)
            initial_participants = activities[activity_name]["participants"].copy()
        
        # Delete one participant
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": other_email}
        )
        
        assert response.status_code == 200
        
        # Verify the deleted email is gone
        assert other_email not in activities[activity_name]["participants"]
        
        # Verify other emails remain (except the one we deleted)
        for participant in initial_participants:
            if participant != other_email:
                assert participant in activities[activity_name]["participants"]


class TestErrorHandling:
    """Tests for error handling scenarios"""

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that posting to a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Activity not found"

    def test_delete_from_nonexistent_activity_returns_404(self):
        """Test that deleting from a non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Activity not found"

    def test_delete_unregistered_participant_returns_404(self):
        """Test that deleting an unregistered participant returns 404"""
        response = client.delete(
            "/activities/Tennis Club/signup",
            params={"email": "nonexistent@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Participant not registered"