import frappe
from frappe.query_builder import DocType
from datetime import date, datetime, timedelta
from frappe.utils import time_diff_in_hours
from frappe.qb import DocType

today = date.today()


@frappe.whitelist()
def create_timesheet(**args):
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    overtime = 0
    attendance_data = fetch_attendance_data(start_date, end_date)
    for attendance in attendance_data:







def fetch_attendance_data(start_date, end_date):
    # Define the Attendance DocType


    # Execute the query
    result = query.run(as_dict=True)
    return result


def over_time(shift, in_time, out_time):
    default_shift_type = frappe.get_doc("Shift Type", shift)
    today = date.today()
    first_in_datetime = datetime.combine(today, (in_time).time())
    last_out_datetime = datetime.combine(today, (out_time).time())
    shift_start_datetime = datetime.combine(today, (datetime.min + default_shift_type.start_time).time())
    shift_end_datetime = datetime.combine(today, (datetime.min + default_shift_type.end_time).time())
    # Adjust first_in_datetime if it's earlier than shift start
    if first_in_datetime < shift_start_datetime:
        first_in_datetime = shift_start_datetime

    over_time = (last_out_datetime - shift_end_datetime).total_seconds() / 3600
    return over_time

def timesheet(attendance_data):
    doc = frappe.new_doc("Timesheet")
    doc.employee = employee.name
    doc.start_date = first_in_datetime
    doc.end_date = last_out_datetime
    doc.attendance = doc.name
    doc = timesheet_doc.append("time_logs", {})
    doc.activity_type = "Execution"
    doc.from_time = first_in_datetime
    doc.to_time = last_out_datetime
    doc.checkout_time = last_out_datetime
    doc.over_time = over_time
    doc.save()  # Save Timesheet

# =====================================to try

def create_timesheets_for_employees(start_date, end_date):
    Attendance = DocType("Attendance")
    # Build the query
    query = (
        frappe.qb.from_(Attendance)
        .select(
            Attendance.in_time,
            Attendance.out_time,
            Attendance.department,
            Attendance.name,
            Attendance.employee,
            Attendance.shift
        )
        .where(
            (Attendance.attendance_date >= start_date)
            & (Attendance.attendance_date <= end_date)
            & (Attendance.department == "Production")
            & Attendance.in_time.isnotnull()
            & Attendance.out_time.isnotnull()
        )
    )

    attendance_data = query.run(as_dict=True)

    # Group attendances by employee
    employee_attendances = {}
    for record in attendance_data:
        overtime = over_time(attendance.shift, attendance.in_time, attendance.out_time)
        if overtime > 0.5 and attendance.department == "Production":
            employee = record["employee"]
            if employee not in employee_attendances:
                employee_attendances[employee] = []
            record["over_time"] = overtime
            employee_attendances[employee].append(record)

    # Create a Timesheet for each employee
    for employee, attendances in employee_attendances.items():
        # Create a new Timesheet
        timesheet_doc = frappe.new_doc("Timesheet")
        timesheet_doc.employee = employee
        timesheet_doc.start_date = start_date
        timesheet_doc.end_date = end_date

        # Add attendance entries to the child table
        for attendance in attendances:
            timesheet_detail = timesheet_doc.append("time_logs", {})
            timesheet_detail.activity_type = "Execution"
            timesheet_detail.from_time = attendance["in_time"]
            timesheet_detail.to_time = attendance["out_time"]
            timesheet_detail.attendance = attendance["attendance_name"]

        # Save the Timesheet
        timesheet_doc.save()
        frappe.db.commit()  # Commit to save changes to the database

