import frappe
from datetime import datetime, date
today = date.today()

def custom_before_submit(doc, method):
    if not doc.in_time or not doc.out_time:
        return  # Skip processing if in_time or out_time is missing

    employee = frappe.get_doc("Employee", doc.employee)
    if not doc.shift:
        frappe.throw("Shift Type is required for Attendance submission.")

    default_shift_type = frappe.get_doc("Shift Type", doc.shift)

    # Combine date and time for calculations
    today = date.today()
    first_in_datetime = datetime.combine(today, (doc.in_time).time())  # Use .time() to extract time
    last_out_datetime = datetime.combine(today, (doc.out_time).time())  # Use .time() to extract time
    shift_start_datetime = datetime.combine(today, (datetime.min + default_shift_type.start_time).time())
    shift_end_datetime = datetime.combine(today, (datetime.min + default_shift_type.end_time).time())

    # Adjust first_in_datetime if it's earlier than shift start
    if first_in_datetime < shift_start_datetime:
        first_in_datetime = shift_start_datetime

    # Calculate overtime
    over_time = max((last_out_datetime - shift_end_datetime).total_seconds() / 3600, 0)

    if over_time > 0.5 and employee.department == "Production":
        # Create new Timesheet
        timesheet_doc = frappe.new_doc("Timesheet")
        timesheet_doc.employee = employee.name
        timesheet_doc.start_time = first_in_datetime
        timesheet_doc.end_time = last_out_datetime
        timesheet_detail = timesheet_doc.append("time_logs", {})
        timesheet_detail.activity_type = "Execution"
        timesheet_detail.from_time = first_in_datetime
        timesheet_detail.to_time = last_out_datetime
        timesheet_detail.hours = over_time
        timesheet_doc.save()  # Save Timesheet

        doc.custom_over_time = over_time  # Assign overtime to the Attendance doc


