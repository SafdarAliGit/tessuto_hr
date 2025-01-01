import frappe
from datetime import datetime, date

today = date.today()


def custom_on_submit(doc, method):
    first_in = doc.in_time
    last_out = doc.out_time
    if first_in and last_out:
        employee = frappe.get_doc("Employee", doc.employee)
        shift = doc.shift

        if not shift:
            frappe.throw("Shift Type Not Found in Employee Checkin")

        default_shift_type = frappe.get_doc("Shift Type", shift)
        first_in_datetime = datetime.combine(today, first_in.time())
        last_out_datetime = datetime.combine(today, last_out.time())
        shift_start_datetime = datetime.combine(today, (datetime.min + default_shift_type.start_time).time())
        shift_end_datetime = datetime.combine(today, (datetime.min + default_shift_type.end_time).time())

        if first_in_datetime < shift_start_datetime:
            first_in_datetime = shift_start_datetime

        over_time = (last_out_datetime - shift_end_datetime).total_seconds() / 3600

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
            timesheet_detail.checkout_time = last_out_datetime
            timesheet_detail.hours = over_time
            timesheet_doc.save()
        doc.custom_over_time = over_time
        doc.save()

