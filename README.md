## Setup
1. After cloning this repository, cd into it.
2. Set up virtual environment via ```python3 -m venv env``` 
3. Activate the virtual environment via ```source env/bin/activate```
4. If it's properly set up, ```which python``` should point to a python under api-skeleton/env.
5. Install dependencies via ```pip install -r requirements.txt```

## Starting local flask server
Make sure your virtual environment is activated, then run:
```bash
flask --app src.app run --host=0.0.0.0 -p 8000
```

By default, Flask runs with port 5000, but some MacOS services now listen on that port.

## Running unit tests
All the tests can be run via ```pytest``` under api-skeleton directory.

## API Endpoints

### Get Doctors
**GET** `/api/doctors`
```bash
curl http://127.0.0.1:8000/api/doctors
```

### Create Appointment
**POST** `/api/appointments`
```bash
curl -X POST http://127.0.0.1:8000/api/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": 1,
    "start_time": "2024-01-15T10:00:00",
    "duration_minutes": 30,
    "patient_name": "John Doe"
  }'
```

### Get All Appointments
**GET** `/api/appointments`
```bash
curl http://127.0.0.1:8000/api/appointments
```

### Get Doctor Appointments (time window)
**GET** `/api/appointments/doctor/{doctor_id}?start_time={start}&end_time={end}`
```bash
curl "http://127.0.0.1:8000/api/appointments/doctor/1?start_time=2024-01-15T08:00:00&end_time=2024-01-15T18:00:00"
```

### Find Next Available Slot
**GET** `/api/appointments/next-available?after_time={time}&duration_minutes={duration}`
```bash
curl "http://127.0.0.1:8000/api/appointments/next-available?after_time=2024-01-15T10:00:00&duration_minutes=30"
```

## Code Structure
This is meant to be barebones.

* src/app.py contains the code for setting up the flask app.
* src/endpoints.py contains all the code for enpoints.
* src/models.py contains all the database model definitions.
* src/extensions.py sets up the extensions (https://flask.palletsprojects.com/en/2.0.x/extensions/)