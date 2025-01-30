from datetime import datetime, timedelta


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json == {"data": "OK"}


def test_create_appointment_success(client):
    """Test creating a valid appointment"""
    appointment_data = {
        "doctor_id": 1,
        "start_time": "2024-01-30T10:00:00",
        "duration_minutes": 30,
        "patient_name": "John Doe",
    }
    response = client.post("/api/appointments", json=appointment_data)
    assert response.status_code == 200
    data = response.json
    assert data["doctor_name"] == "Strange"
    assert data["patient_name"] == "John Doe"
    assert data["duration_minutes"] == 30


def test_create_appointment_outside_hours(client):
    """Test creating an appointment outside working hours"""
    appointment_data = {
        "doctor_id": 1,
        "start_time": "2024-01-30T18:00:00",  # After 5 PM
        "duration_minutes": 30,
        "patient_name": "John Doe",
    }
    response = client.post("/api/appointments", json=appointment_data)
    assert response.status_code == 400
    assert "not working at this time" in response.json["error"].lower()


def test_create_appointment_on_weekend(client):
    """Test creating an appointment on weekend"""
    appointment_data = {
        "doctor_id": 1,
        "start_time": "2024-02-03T10:00:00",  # Saturday
        "duration_minutes": 30,
        "patient_name": "John Doe",
    }
    response = client.post("/api/appointments", json=appointment_data)
    assert response.status_code == 400
    assert "not working at this time" in response.json["error"].lower()


def test_create_appointment_conflict(client):
    """Test creating an appointment that conflicts with existing one"""
    # Create first appointment
    appointment1 = {
        "doctor_id": 1,
        "start_time": "2024-01-30T10:00:00",
        "duration_minutes": 30,
        "patient_name": "John Doe",
    }
    client.post("/api/appointments", json=appointment1)

    # Try to create overlapping appointment
    appointment2 = {
        "doctor_id": 1,
        "start_time": "2024-01-30T10:15:00",  # Overlaps with first appointment
        "duration_minutes": 30,
        "patient_name": "Jane Smith",
    }
    response = client.post("/api/appointments", json=appointment2)
    assert response.status_code == 409  # Conflict
    assert "conflict" in response.json["error"].lower()


def test_get_doctor_appointments(client):
    """Test getting appointments for a specific doctor"""
    # Create appointments for both doctors
    appointments = [
        {
            "doctor_id": 1,
            "start_time": "2024-01-30T10:00:00",
            "duration_minutes": 30,
            "patient_name": "John Doe",
        },
        {
            "doctor_id": 2,
            "start_time": "2024-01-30T09:00:00",
            "duration_minutes": 45,
            "patient_name": "Jane Smith",
        },
    ]
    for appt in appointments:
        client.post("/api/appointments", json=appt)

    # Get appointments for Dr. Strange (id=1)
    response = client.get(
        "/api/appointments/doctor/1",
        query_string={
            "start_time": "2024-01-30T00:00:00",
            "end_time": "2024-01-30T23:59:59",
        },
    )
    assert response.status_code == 200
    data = response.json
    assert len(data) == 1
    assert data[0]["doctor_name"] == "Strange"
    assert data[0]["patient_name"] == "John Doe"


def test_get_next_available_slot(client):
    """Test finding next available appointment slot"""
    # Create an appointment
    appointment = {
        "doctor_id": 1,
        "start_time": "2024-01-30T09:00:00",  # Earlier appointment
        "duration_minutes": 30,
        "patient_name": "John Doe",
    }
    client.post("/api/appointments", json=appointment)

    # Find next available slot
    response = client.get(
        "/api/appointments/next-available",
        query_string={"after_time": "2024-01-30T09:00:00", "duration_minutes": 30},
    )
    assert response.status_code == 200
    data = response.json
    assert data["doctor_name"] == "Who"  # Dr. Who starts earlier (8 AM)
    assert data["available_time"] == "2024-01-30T09:00:00"  # First available slot
