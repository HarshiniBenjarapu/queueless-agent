```
# Appointment Cancellation &amp; Waitlist Fill Workflow

## Name
appointment_cancellation

## Description
Handles patient requests to cancel an existing appointment, checks for matching waitlisted patients, and automatically offers the freed slot to patients on the waiting list.

## Detailed Steps
When a patient requests to cancel an appointment:
1. **Verify Patient Identity**: Use `get_patient_details(patient_id)` to check patient status and details.
2. **Check Clinic Schedule**: Use `check_clinic_calendar(doctor_name)` to locate the appointment slot.
3. **Cancel &amp; Notify**: Confirm the cancellation with the patient and send a notification confirmation using `send_patient_notification(patient_id, message)`.
4. **Offer Slot to Waitlist**: Check if any patients are currently on the waiting list (e.g., status `waiting_list`) and offer the newly opened slot to optimize doctor calendar utilization.

