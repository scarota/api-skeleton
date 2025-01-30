from src.extensions import db
from flask import jsonify
from datetime import datetime


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    start_time = db.Column(db.Time, nullable=False)  # Daily start time
    end_time = db.Column(db.Time, nullable=False)  # Daily end time
    appointments = db.relationship("Appointment", backref="doctor", lazy=True)

    def json(self):
        return jsonify(
            {
                "id": self.id,
                "name": self.name,
                "start_time": self.start_time.strftime("%H:%M"),
                "end_time": self.end_time.strftime("%H:%M"),
            }
        )

    def is_working_at(self, dt: datetime) -> bool:
        """Check if the doctor is working at a given datetime"""
        # Only working Monday (0) through Friday (4)
        if dt.weekday() > 4:
            return False
        current_time = dt.time()
        return self.start_time <= current_time <= self.end_time


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)  # Duration in minutes
    patient_name = db.Column(db.String, nullable=False)

    def end_time(self) -> datetime:
        """Calculate the end time of the appointment"""
        from datetime import timedelta

        return self.start_time + timedelta(minutes=self.duration_minutes)

    def json(self):
        return jsonify(
            {
                "id": self.id,
                "doctor_id": self.doctor_id,
                "doctor_name": self.doctor.name,
                "start_time": self.start_time.isoformat(),
                "duration_minutes": self.duration_minutes,
                "end_time": self.end_time().isoformat(),
                "patient_name": self.patient_name,
            }
        )

    def has_conflict(self, other: "Appointment") -> bool:
        """Check if this appointment conflicts with another"""
        if self.doctor_id != other.doctor_id:
            return False
        return self.start_time < other.end_time() and self.end_time() > other.start_time
