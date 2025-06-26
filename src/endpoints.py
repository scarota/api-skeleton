from flask import Blueprint, jsonify
from http import HTTPStatus
from datetime import time, timedelta
from src.extensions import db
from src.models import Doctor, Appointment
from webargs import fields, validate
from webargs.flaskparser import use_args
from sqlalchemy import and_

# New API blueprint for appointments
api = Blueprint("api", __name__)


@api.route("/")
def index():
    return {"data": "OK"}


@api.route("/appointments", methods=["POST"])
@use_args(
    {
        "doctor_id": fields.Int(required=True),
        "start_time": fields.DateTime(required=True),
        "duration_minutes": fields.Int(required=True, validate=validate.Range(min=1)),
        "patient_name": fields.Str(required=True),
    }
)
def create_appointment(args):
    """Create a new appointment"""
    # Get the doctor
    doctor = Doctor.query.get_or_404(args["doctor_id"])

    # Create proposed appointment
    new_appointment = Appointment(
        doctor_id=args["doctor_id"],
        start_time=args["start_time"],
        duration_minutes=args["duration_minutes"],
        patient_name=args["patient_name"],
    )

    # Check if doctor is working
    if not doctor.is_working_at(new_appointment.start_time) or not doctor.is_working_at(
        new_appointment.end_time()
    ):
        return (
            jsonify({"error": "Doctor is not working at this time"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Check for conflicts
    existing_appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    for existing in existing_appointments:
        if new_appointment.has_conflict(existing):
            return (
                jsonify({"error": "Appointment conflicts with existing booking"}),
                HTTPStatus.CONFLICT,
            )

    # Save appointment
    db.session.add(new_appointment)
    db.session.commit()
    return new_appointment.json()


@api.route("/appointments", methods=["GET"])
def get_all_appointments():
    """Get all appointments"""
    appointments = Appointment.query.order_by(Appointment.start_time).all()
    return jsonify([appt.json().get_json() for appt in appointments])


@api.route("/appointments/doctor/<int:doctor_id>")
@use_args(
    {
        "start_time": fields.DateTime(required=True),
        "end_time": fields.DateTime(required=True),
    },
    location="query",
)
def get_doctor_appointments(args, doctor_id):
    """Get all appointments for a doctor within a time window"""
    Doctor.query.get_or_404(doctor_id)  # Verify doctor exists

    appointments = Appointment.query.filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time >= args["start_time"],
            Appointment.start_time <= args["end_time"],
        )
    ).all()

    return jsonify([appt.json().json for appt in appointments])


@api.route("/appointments/next-available")
@use_args(
    {
        "after_time": fields.DateTime(required=True),
        "duration_minutes": fields.Int(required=True, validate=validate.Range(min=1)),
    },
    location="query",
)
def get_next_available(args):
    """Find the first available appointment slot after the specified time"""
    doctors = Doctor.query.all()
    earliest_slot = None
    selected_doctor = None

    for doctor in doctors:
        # Get all appointments for this doctor after the specified time
        appointments = (
            Appointment.query.filter(
                and_(
                    Appointment.doctor_id == doctor.id,
                    Appointment.start_time >= args["after_time"],
                )
            )
            .order_by(Appointment.start_time)
            .all()
        )

        # Start checking from after_time
        check_time = args["after_time"]

        # Keep checking until we find a slot or reach end of day
        while check_time.time() <= doctor.end_time:
            # Skip if outside working hours
            if not doctor.is_working_at(check_time):
                check_time += timedelta(days=1)
                check_time = check_time.replace(
                    hour=doctor.start_time.hour, minute=doctor.start_time.minute
                )
                continue

            # Create potential appointment
            potential = Appointment(
                doctor_id=doctor.id,
                start_time=check_time,
                duration_minutes=args["duration_minutes"],
                patient_name="TEST",  # Not saved, just for conflict checking
            )

            # Check for conflicts
            has_conflict = False
            for existing in appointments:
                if potential.has_conflict(existing):
                    has_conflict = True
                    # Move check_time to end of conflicting appointment
                    check_time = existing.end_time()
                    break

            if not has_conflict:
                # Found a slot! Check if it's the earliest so far
                if earliest_slot is None or check_time < earliest_slot:
                    earliest_slot = check_time
                    selected_doctor = doctor
                break

            # If we had a conflict, continue from the new check_time
            continue

    if earliest_slot is None or selected_doctor is None:
        return jsonify({"error": "No available slots found"}), HTTPStatus.NOT_FOUND

    return jsonify(
        {
            "doctor_id": selected_doctor.id,
            "doctor_name": selected_doctor.name,
            "available_time": earliest_slot.isoformat(),
            "duration_minutes": args["duration_minutes"],
        }
    )


@api.route("/doctors", methods=["GET"])
def get_doctors():
    """Get all doctors and their working hours"""
    doctors = Doctor.query.all()
    return jsonify([doc.json().json for doc in doctors])
