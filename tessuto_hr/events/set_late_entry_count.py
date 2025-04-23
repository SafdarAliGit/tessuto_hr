import frappe
from datetime import datetime
from frappe.query_builder import DocType, functions as fn

@frappe.whitelist()
def set_late_entry_count(**args):
    start_date = args.get('start_date')
    end_date = args.get('end_date')

    late_entry_sum = get_late_entry_sum(start_date, end_date)
    early_exit_sum = get_early_exit_sum(start_date, end_date)
    days_for_absent_mark = frappe.db.get_single_value("Attendance Settings", 'days_for_absent_mark')

    # Update late entry values
    for row in late_entry_sum:
        if row["custom_total_late_entry_count"] > 0:
            frappe.db.set_value(
                "Employee",
                row["employee"],
                {
                    "custom_total_late_entry_count": row["custom_total_late_entry_count"],
                    "custom_total_late_entry_absent": (row['custom_total_late_entry_count'] // days_for_absent_mark)
                }
            )

    # Update early exit values
    for row in early_exit_sum:
        if row["custom_total_early_exit_count"] > 0:
            frappe.db.set_value(
                "Employee",
                row["employee"],
                {
                    "custom_total_early_exit_count": row["custom_total_early_exit_count"],
                    "custom_total_early_exit_absent": (row['custom_total_early_exit_count'] // days_for_absent_mark)
                }
            )

    frappe.db.commit()
    return frappe.msgprint(
        f"Updated Late Entry and Early Exit Counts in respective Employees successfully from {start_date} to {end_date}."
    )


def get_late_entry_sum(start_date, end_date):
    # Define the Attendance DocType
    Attendance = DocType("Attendance")

    # Construct the query
    query = (
        frappe.qb.from_(Attendance)
        .select(
            Attendance.employee,
            fn.Sum(Attendance.late_entry).as_("custom_total_late_entry_count")
        )
        .where(
            (Attendance.status == "Present") &
            (Attendance.attendance_date >= start_date) &
            (Attendance.attendance_date <= end_date)
        )
        .groupby(Attendance.employee)
        .having(fn.Sum(Attendance.late_entry) > 0)
    )

    # Execute the query
    results = query.run(as_dict=True)
    return results

def get_early_exit_sum(start_date, end_date):
    # Define the Attendance DocType
    Attendance = DocType("Attendance")

    # Construct the query
    query = (
        frappe.qb.from_(Attendance)
        .select(
            Attendance.employee,
            fn.Sum(Attendance.early_exit).as_("custom_total_early_exit_count")
        )
        .where(
            (Attendance.status == "Present") &
            (Attendance.attendance_date >= start_date) &
            (Attendance.attendance_date <= end_date)
        )
        .groupby(Attendance.employee)
        .having(fn.Sum(Attendance.early_exit) > 0)
    )

    # Execute the query
    results = query.run(as_dict=True)
    return results
