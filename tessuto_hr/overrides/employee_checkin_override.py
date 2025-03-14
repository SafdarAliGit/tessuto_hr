from datetime import datetime, date
from frappe.utils import getdate

today = date.today()
import frappe
from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin
from tessuto_hr.overrides.shift_hour import shift_hour


class EmployeeCheckinOverride(EmployeeCheckin):
    def after_save(self):
        if self.log_type == "OUT":
            employee = frappe.get_doc("Employee", self.employee)
            self.shift = employee.default_shift

            if not self.shift:
                frappe.throw("Shift Type Not Found in Employee Checkin")

            checkin_list_with_shift = frappe.db.sql(
                """
                SELECT log_type, time, name 
                FROM `tabEmployee Checkin`
                WHERE employee = %s AND DATE(time) = %s AND shift = %s
                """,
                (self.employee, getdate(self.time), self.shift),
                as_dict=1
            )
            default_shift_type = frappe.get_doc("Shift Type", self.shift)
            first_in = next((record for record in checkin_list_with_shift if record['log_type'] == 'IN'), None)
            last_out = next((record for record in reversed(checkin_list_with_shift) if record['log_type'] == 'OUT'),
                            None)

            first_in_time = first_in['time']
            last_out_time = last_out['time']
            first_in_name = first_in['name']
            last_out_name = last_out['name']

            first_in_datetime = datetime.combine(today, first_in_time.time())
            last_out_datetime = datetime.combine(today, last_out_time.time())
            start_datetime = datetime.combine(today, (datetime.min + default_shift_type.start_time).time())
            end_datetime = datetime.combine(today, (datetime.min + default_shift_type.end_time).time())

            if first_in_datetime < start_datetime:
                first_in_datetime = start_datetime

            over_time = (last_out_datetime - end_datetime).total_seconds() / 3600

            dailyovertime_exists = frappe.db.exists("Daily Over Time", {
                "date": getdate(self.time),
                "employee_id": self.employee
            })
            print(f"Over Time: {over_time}, Employee Department: {employee.department}, Daily Over Time Exists: {dailyovertime_exists}")
            if over_time > 0.5 and employee.department == "Production":
                if dailyovertime_exists:
                    # Update existing Daily Over Time
                    dot = frappe.get_doc("Daily Over Time", dailyovertime_exists)
                    dot.check_in_time = first_in_datetime
                    dot.check_out_time = last_out_datetime
                    dot.employee_shift = self.shift
                    dot.over_time_hours = over_time
                    dot.check_in_ref = first_in_name
                    dot.check_out_ref = last_out_name
                    dot.save()
                else:
                    # Create new Daily Over Time
                    dot = frappe.new_doc("Daily Over Time")
                    dot.employee_id = self.employee
                    dot.date = getdate(self.time)
                    dot.check_in_time = first_in_datetime
                    dot.check_out_time = last_out_datetime
                    dot.employee_shift = self.shift
                    dot.over_time_hours = over_time
                    dot.check_in_ref = first_in_name
                    dot.check_out_ref = last_out_name
                    dot.save()

                timesheet_exists = frappe.db.exists("Timesheet", {
                    "employee": self.employee,
                    "start_date": getdate(self.time)
                })

                if timesheet_exists:
                    # Update existing Timesheet
                    timesheet_doc = frappe.get_doc("Timesheet", timesheet_exists)
                    timesheet_doc.start_time = first_in_datetime
                    timesheet_doc.end_time = last_out_datetime
                    if timesheet_doc.time_logs:
                        timesheet_detail = timesheet_doc.time_logs[0]
                        timesheet_detail.from_time = first_in_datetime
                        timesheet_detail.to_time = last_out_datetime
                        timesheet_detail.checkout_time = last_out_datetime
                        timesheet_detail.hours = over_time
                    timesheet_doc.save()
                else:
                    # Create new Timesheet
                    timesheet_doc = frappe.new_doc("Timesheet")
                    timesheet_doc.employee = self.employee
                    timesheet_doc.start_time = first_in_datetime
                    timesheet_doc.end_time = last_out_datetime
                    timesheet_detail = timesheet_doc.append("time_logs", {})
                    timesheet_detail.activity_type = "Execution"
                    timesheet_detail.from_time = first_in_datetime
                    timesheet_detail.to_time = last_out_datetime
                    timesheet_detail.checkout_time = last_out_datetime
                    timesheet_detail.hours = over_time
                    timesheet_doc.save()
