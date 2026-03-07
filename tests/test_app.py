import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def client():
    db_fd = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_fd.name
    db_fd.close()
    os.environ["DB_NAME"] = db_path
    from app import app, init_db
    app.config["TESTING"] = True
    with app.app_context():
        init_db()
    with app.test_client() as c:
        yield c
    os.unlink(db_path)

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200

def test_login_valid(client):
    res = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200

def test_login_invalid(client):
    res = client.post("/api/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401

def test_list_clients_empty(client):
    res = client.get("/api/clients")
    assert res.get_json() == []

def test_create_client(client):
    res = client.post("/api/clients", json={"name": "Arjun", "weight": 75.0, "program": "Fat Loss"})
    assert res.status_code == 201

def test_duplicate_client(client):
    client.post("/api/clients", json={"name": "Arjun", "weight": 75.0, "program": "Fat Loss"})
    res = client.post("/api/clients", json={"name": "Arjun", "weight": 75.0, "program": "Fat Loss"})
    assert res.status_code == 409

def test_get_client(client):
    client.post("/api/clients", json={"name": "Priya", "weight": 60.0, "program": "Beginner"})
    res = client.get("/api/clients/Priya")
    assert res.status_code == 200

def test_get_missing_client(client):
    res = client.get("/api/clients/Ghost")
    assert res.status_code == 404

def test_delete_client(client):
    client.post("/api/clients", json={"name": "Ravi", "weight": 70.0, "program": "Muscle Gain"})
    res = client.delete("/api/clients/Ravi")
    assert res.status_code == 200

def test_list_programs(client):
    res = client.get("/api/programs")
    assert "Fat Loss" in res.get_json()

def test_log_progress(client):
    client.post("/api/clients", json={"name": "Dev", "weight": 70.0, "program": "Fat Loss"})
    res = client.post("/api/clients/Dev/progress", json={"adherence": 80})
    assert res.status_code == 201

def test_invalid_adherence(client):
    client.post("/api/clients", json={"name": "Dev", "weight": 70.0, "program": "Fat Loss"})
    res = client.post("/api/clients/Dev/progress", json={"adherence": 150})
    assert res.status_code == 400

def test_log_workout(client):
    client.post("/api/clients", json={"name": "Sam", "weight": 80.0, "program": "Muscle Gain"})
    res = client.post("/api/clients/Sam/workouts", json={"workout_type": "Strength", "duration_min": 60})
    assert res.status_code == 201