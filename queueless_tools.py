
from strands import tool

PATIENTS = {
    "P-1001": {
        "name": "Anil Kumar",
        "phone": "+91-9876543210",
        "email": "anil.k@email.com",
        "preferred_slot": "morning",
        "status": "scheduled",
    },
    "P-1002": {
        "name": "Priya Sharma",
        "phone": "+91-9876543211",
        "email": "priya.s@email.com",
        "preferred_slot": "evening",
        "status": "waiting_list",
    },
}

CLINIC_SLOTS = [
    {"slot_id": "SLOT-101", "doctor": "Dr. Rao", "date": "2025-09-15", "time": "09:30 AM", "status": "Available"},
    {"slot_id": "SLOT-102", "doctor": "Dr. Rao", "date": "2025-09-20", "time": "11:00 AM", "status": "Booked"},
]

@tool
def get_patient_details(patient_id: str) -> str:
    """Look up patient information and preferences by patient ID."""
    patient = PATIENTS.get(patient_id)
    if not patient:
        return f"No patient record found for ID {patient_id}"
    return (
        f"Patient: {patient['name']}\n"
        f"Phone: {patient['phone']}\n"
        f"Email: {patient['email']}\n"
        f"Preference: {patient['preferred_slot']}\n"
        f"Status: {patient['status']}"
    )

@tool
def check_clinic_calendar(doctor_name: str) -> str:
    """Check available and cancelled appointment slots for a specific doctor."""
    slots = [s for s in CLINIC_SLOTS if doctor_name.lower() in s["doctor"].lower()]
    if not slots:
        return f"No calendar entries found for {doctor_name}"
    lines = []
    for slot in slots:
        lines.append(f"[{slot['status']}] Slot {slot['slot_id']}: {slot['date']} at {slot['time']}")
    return "\n".join(lines)

@tool
def reschedule_appointment(patient_id: str, appointment_id: str, new_slot_time: str) -> str:
    """Reschedule a patient's appointment to a new slot."""
    return f"Appointment {appointment_id} for patient {patient_id} successfully rescheduled to {new_slot_time}."

@tool
def cancel_appointment(patient_id: str, doctor_name: str) -> str:
    """Cancels a scheduled patient appointment with a specific doctor."""
    return f"Appointment for patient {patient_id} with {doctor_name} has been successfully cancelled."

@tool
def send_patient_notification(patient_id: str, message: str)-> str:
    """Send an SMS/Email notification or appointment reminder to a patient."""
    return f"Notification sent to patient {patient_id}: '{message}'"

