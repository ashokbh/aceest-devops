"""
ACEest Fitness & Gym - Pytest Unit Test Suite
Tests all Flask API endpoints and core business logic.
"""

import pytest
import json
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, init_db, calculate_calories, validate_client_data, PROGRAMS


# ---------- FIXTURES ----------

@pytest.fixture
def client():
    """Flask test client with a fresh file DB per test."""
    import tempfile
    db_fd = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_fd.name
    db_fd.close()
    os.environ["DB_NAME"] = db_path

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    with app.app_context():
        init_db()

    with app.test_client() as c:
        yield c

    os.unlink(db_path)


@pytest.fixture
def saved_client(client):
    """Creates a client and returns the test client + client data."""
    payload = {
        "name": "Arjun Kumar",
        "age": 28,
        "weight": 75.0,
        "height": 175.0,
        "program": "Fat Loss"
    }
    client.post("/api/clients", json=payload)
    return client, payload


# ============================================================
# 1. HEALTH CHECK
# ============================================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200

    def test_health_returns_correct_body(self, client):
        res = client.get("/health")
        data = res.get_json()
        assert data["status"] == "healthy"
        assert "ACEest" in data["app"]


# ============================================================
# 2. UNIT TESTS – BUSINESS LOGIC (no DB / HTTP)
# ============================================================

class TestCalculateCalories:
    def test_fat_loss_factor(self):
        assert calculate_calories(70.0, "Fat Loss") == 70 * 22

    def test_muscle_gain_factor(self):
        assert calculate_calories(80.0, "Muscle Gain") == 80 * 35

    def test_beginner_factor(self):
        assert calculate_calories(60.0, "Beginner") == 60 * 26

    def test_unknown_program_returns_zero(self):
        assert calculate_calories(70.0, "Yoga") == 0

    def test_zero_weight(self):
        assert calculate_calories(0.0, "Fat Loss") == 0

    def test_returns_integer(self):
        result = calculate_calories(72.5, "Fat Loss")
        assert isinstance(result, int)


class TestValidateClientData:
    def test_valid_data_passes(self):
        ok, msg = validate_client_data({"name": "John", "program": "Fat Loss", "weight": 70})
        assert ok is True
        assert msg == ""

    def test_missing_name_fails(self):
        ok, msg = validate_client_data({"program": "Fat Loss"})
        assert ok is False
        assert "Name" in msg

    def test_empty_name_fails(self):
        ok, msg = validate_client_data({"name": "  ", "program": "Fat Loss"})
        assert ok is False

    def test_missing_program_fails(self):
        ok, msg = validate_client_data({"name": "John"})
        assert ok is False
        assert "Program" in msg

    def test_invalid_program_fails(self):
        ok, msg = validate_client_data({"name": "John", "program": "Zumba"})
        assert ok is False
        assert "Invalid program" in msg

    def test_negative_weight_fails(self):
        ok, msg = validate_client_data({"name": "John", "program": "Fat Loss", "weight": -10})
        assert ok is False

    def test_non_numeric_weight_fails(self):
        ok, msg = validate_client_data({"name": "John", "program": "Fat Loss", "weight": "heavy"})
        assert ok is False


# ============================================================
# 3. AUTH ENDPOINTS
# ============================================================

class TestAuth:
    def test_login_valid_credentials(self, client):
        res = client.post("/api/login", json={"username": "admin", "password": "admin123"})
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"

    def test_login_returns_role(self, client):
        res = client.post("/api/login", json={"username": "admin", "password": "admin123"})
        assert res.get_json()["role"] == "Admin"

    def test_login_wrong_password(self, client):
        res = client.post("/api/login", json={"username": "admin", "password": "wrong"})
        assert res.status_code == 401

    def test_login_unknown_user(self, client):
        res = client.post("/api/login", json={"username": "nobody", "password": "pass"})
        assert res.status_code == 401

    def test_logout(self, client):
        res = client.post("/api/logout")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"


# ============================================================
# 4. CLIENT CRUD
# ============================================================

class TestClientCreate:
    def test_create_client_success(self, client):
        res = client.post("/api/clients", json={
            "name": "Priya", "age": 30, "weight": 60.0, "program": "Beginner"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "ok"
        assert "calories" in data

    def test_create_client_calories_computed(self, client):
        res = client.post("/api/clients", json={
            "name": "Vikram", "weight": 80.0, "program": "Muscle Gain"
        })
        data = res.get_json()
        assert data["calories"] == 80 * 35

    def test_create_duplicate_client_fails(self, client):
        payload = {"name": "Dup", "weight": 70.0, "program": "Fat Loss"}
        client.post("/api/clients", json=payload)
        res = client.post("/api/clients", json=payload)
        assert res.status_code == 409

    def test_create_missing_name_fails(self, client):
        res = client.post("/api/clients", json={"program": "Fat Loss", "weight": 70})
        assert res.status_code == 400

    def test_create_invalid_program_fails(self, client):
        res = client.post("/api/clients", json={"name": "X", "program": "CrossFit", "weight": 70})
        assert res.status_code == 400


class TestClientRead:
    def test_list_clients_empty(self, client):
        res = client.get("/api/clients")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_list_clients_after_create(self, saved_client):
        c, _ = saved_client
        res = c.get("/api/clients")
        assert len(res.get_json()) == 1

    def test_get_client_by_name(self, saved_client):
        c, data = saved_client
        res = c.get(f"/api/clients/{data['name']}")
        assert res.status_code == 200
        assert res.get_json()["name"] == data["name"]

    def test_get_nonexistent_client(self, client):
        res = client.get("/api/clients/Ghost")
        assert res.status_code == 404


class TestClientUpdate:
    def test_update_client(self, saved_client):
        c, data = saved_client
        res = c.put(f"/api/clients/{data['name']}", json={
            "weight": 72.0, "program": "Muscle Gain", "age": 29
        })
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"

    def test_update_recalculates_calories(self, saved_client):
        c, data = saved_client
        res = c.put(f"/api/clients/{data['name']}", json={
            "weight": 80.0, "program": "Muscle Gain"
        })
        assert res.get_json()["calories"] == 80 * 35

    def test_update_nonexistent_client(self, client):
        res = client.put("/api/clients/Nobody", json={"weight": 70, "program": "Fat Loss"})
        assert res.status_code == 404


class TestClientDelete:
    def test_delete_client(self, saved_client):
        c, data = saved_client
        res = c.delete(f"/api/clients/{data['name']}")
        assert res.status_code == 200

    def test_delete_removes_from_list(self, saved_client):
        c, data = saved_client
        c.delete(f"/api/clients/{data['name']}")
        res = c.get("/api/clients")
        assert res.get_json() == []

    def test_delete_nonexistent_client(self, client):
        res = client.delete("/api/clients/NoOne")
        assert res.status_code == 404


# ============================================================
# 5. PROGRAMS ENDPOINTS
# ============================================================

class TestPrograms:
    def test_list_programs(self, client):
        res = client.get("/api/programs")
        assert res.status_code == 200
        programs = res.get_json()
        assert "Fat Loss" in programs
        assert "Muscle Gain" in programs
        assert "Beginner" in programs

    def test_program_count(self, client):
        res = client.get("/api/programs")
        assert len(res.get_json()) == len(PROGRAMS)

    def test_get_valid_program_detail(self, client):
        res = client.get("/api/programs/Fat Loss")
        assert res.status_code == 200
        data = res.get_json()
        assert "workout" in data
        assert "diet" in data
        assert "calorie_factor" in data

    def test_get_invalid_program(self, client):
        res = client.get("/api/programs/Pilates")
        assert res.status_code == 404


# ============================================================
# 6. PROGRESS ENDPOINTS
# ============================================================

class TestProgress:
    def test_log_progress(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/progress",
                     json={"adherence": 85})
        assert res.status_code == 201
        assert res.get_json()["status"] == "ok"

    def test_get_progress(self, saved_client):
        c, data = saved_client
        c.post(f"/api/clients/{data['name']}/progress", json={"adherence": 70})
        res = c.get(f"/api/clients/{data['name']}/progress")
        assert res.status_code == 200
        entries = res.get_json()
        assert len(entries) == 1
        assert entries[0]["adherence"] == 70

    def test_log_progress_boundary_zero(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/progress", json={"adherence": 0})
        assert res.status_code == 201

    def test_log_progress_boundary_hundred(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/progress", json={"adherence": 100})
        assert res.status_code == 201

    def test_log_progress_invalid_adherence(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/progress", json={"adherence": 150})
        assert res.status_code == 400

    def test_log_progress_custom_week(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/progress",
                     json={"adherence": 90, "week": "Week 01 - 2025"})
        assert res.get_json()["week"] == "Week 01 - 2025"


# ============================================================
# 7. WORKOUT ENDPOINTS
# ============================================================

class TestWorkouts:
    def test_log_workout(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/workouts",
                     json={"workout_type": "Strength", "duration_min": 60})
        assert res.status_code == 201

    def test_log_workout_missing_type(self, saved_client):
        c, data = saved_client
        res = c.post(f"/api/clients/{data['name']}/workouts",
                     json={"duration_min": 60})
        assert res.status_code == 400

    def test_get_workouts(self, saved_client):
        c, data = saved_client
        c.post(f"/api/clients/{data['name']}/workouts",
               json={"workout_type": "Cardio", "duration_min": 45})
        res = c.get(f"/api/clients/{data['name']}/workouts")
        assert res.status_code == 200
        entries = res.get_json()
        assert len(entries) >= 1
        assert entries[0]["workout_type"] == "Cardio"


# ============================================================
# 8. MEMBERSHIP ENDPOINT
# ============================================================

class TestMembership:
    def test_check_membership_active(self, saved_client):
        c, data = saved_client
        res = c.get(f"/api/clients/{data['name']}/membership")
        assert res.status_code == 200
        result = res.get_json()
        assert result["membership_status"] == "Active"

    def test_check_membership_not_found(self, client):
        res = client.get("/api/clients/Ghost/membership")
        assert res.status_code == 404
