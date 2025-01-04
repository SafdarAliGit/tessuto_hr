import frappe
from frappe import print_sql
from frappe.query_builder import DocType
from datetime import date, datetime, timedelta
from frappe.utils import time_diff_in_hours
from frappe.query_builder import DocType

today = date.today()


@frappe.whitelist()
def create_timesheet(**args):
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    create_timesheets_for_employees(start_date, end_date)
    return frappe.msgprint(
        f"Timesheets created successfully for {start_date} to {end_date}."
    )


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


def create_timesheets_for_employees(start_date, end_date):
    consider_over_time = 0
    department = []
    settings = get_over_time_settings()
    if "error" in settings:
        print(settings["error"])
    else:
        consider_over_time =  settings["consider_over_time"]
        department = [item.department for item in settings["department"]]

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
            & (Attendance.department.isin(department))
            & Attendance.in_time.isnotnull()
            & Attendance.out_time.isnotnull()
        )
    )

    attendance_data = query.run(as_dict=True)

    # Group attendances by employee
    employee_attendances = {}
    for record in attendance_data:
        ts_not_present = timesheet_not_present(record.employee, start_date, end_date)
        overtime = over_time(record.shift, record.in_time, record.out_time)
        if overtime > consider_over_time and record.department in department and ts_not_present:
            employee = record["employee"]
            if employee not in employee_attendances:
                employee_attendances[employee] = []
            record["over_time"] = overtime
            employee_attendances[employee].append(record)

    # Create a Timesheet for each employee
    for employee, attendances in employee_attendances.items():
        # Create a new Timesheet
        sum_over_time = 0
        timesheet_doc = frappe.new_doc("Timesheet")
        timesheet_doc.employee = employee

        # Add attendance entries to the child table
        for attendance in attendances:
            timesheet_detail = timesheet_doc.append("time_logs", {})
            timesheet_detail.activity_type = "Execution"
            timesheet_detail.from_time = attendance["in_time"]
            timesheet_detail.to_time = attendance["out_time"]
            timesheet_detail.custom_checkin_time = attendance["in_time"]
            timesheet_detail.checkout_time = attendance["out_time"]
            timesheet_detail.over_time = attendance["over_time"]
            timesheet_detail.custom_attendance = attendance["name"]
            sum_over_time += attendance["over_time"]

        # Save the Timesheet
        timesheet_doc.custom_over_time = sum_over_time
        timesheet_doc.save()
        frappe.db.commit()  # Commit to save changes to the database


def timesheet_not_present(employee, start_date, end_date):
    """
    Check if a Timesheet record exists for the given employee, start_date, and end_date.
    Returns True if no record is found, False otherwise.
    """
    Timesheet = DocType("Timesheet")

    # Build the query
    query = (
        frappe.qb.from_(Timesheet)
        .select(Timesheet.name)
        .where(
            (Timesheet.employee == employee)
            & (Timesheet.start_date >= start_date)
            & (Timesheet.end_date <= end_date)
        )
    )

    # Execute the query and fetch results
    result = query.run(as_dict=True)

    # Return True if no record is found, False otherwise
    return len(result) == 0


def get_over_time_settings():
    """
    Fetch and return the data from the Over Time Settings single doctype,
    specifically the `consider_over_time` and `department` fields.
    """
    try:
        # Fetch single doctype data
        settings = frappe.get_single("Over Time Settings")

        # Extract relevant fields
        data = {
            "consider_over_time": settings.consider_over_time,
            "department": settings.department if settings.department else []
        }
        return data

    except frappe.DoesNotExistError:
        # Handle the case where the single doctype is not configured
        return {"error": "Over Time Settings single doctype is not configured."}
