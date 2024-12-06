from datetime import datetime, date

today = date.today()
import frappe
from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin
from tessuto_hr.overrides.shift_hour import shift_hour


class EmployeeCheckinOverride(EmployeeCheckin):
    def before_save(self):
        self.shift = "Shift 1"

    def on_update(self):
        employee = frappe.get_doc("Employee", self.employee)
        """ Auto log_type IN Or OUT"""
        checkin_list = frappe.db.sql(
            """
            SELECT name 
            FROM `tabEmployee Checkin`
            WHERE employee = %s AND DATE(time) = %s
            """,
            (self.employee, today),
            as_dict=True
        )

        if checkin_list:
            if len(checkin_list) == 1:
                checkin = frappe.get_doc("Employee Checkin", checkin_list[0].name)
                checkin.db_set("log_type", 'IN', update_modified=False)

            else:
                last_checkin = frappe.get_doc("Employee Checkin", checkin_list[-1].name)
                last_checkin.db_set("log_type", 'OUT', update_modified=False)

                # Calculate Check IN and Check OUT time difference

                if not self.shift:
                    frappe.throw("Shift Type Not Found in Employee Checkin")
                time_difference = 0
                checkin_list_with_shift = frappe.db.sql(
                    """
                    SELECT log_type, time,name 
                    FROM `tabEmployee Checkin`
                    WHERE employee = %s AND DATE(time) = %s AND shift = %s
                    """,
                    (self.employee, today, self.shift),
                    as_dict=1
                )
                default_shift_type = frappe.get_doc("Shift Type", self.shift)
                first_in = next((record for record in checkin_list_with_shift if record['log_type'] == 'IN'), None)
                last_out = next((record for record in reversed(checkin_list_with_shift) if record['log_type'] == 'OUT'),
                                None)

                if not first_in or not last_out:
                    time_difference = 0

                first_in_time = first_in['time']
                last_out_time = last_out['time']
                first_in_name = first_in['name']
                last_out_name = last_out['name']

                first_in_datetime = datetime.combine(today, first_in_time.time())
                last_out_datetime = datetime.combine(today, last_out_time.time())
                start_datetime = datetime.combine(today, (datetime.min + default_shift_type.start_time).time())
                if first_in_datetime < start_datetime:
                    first_in_datetime = start_datetime
                time_difference = (last_out_datetime - first_in_datetime).total_seconds() / 3600

                shift_hours = shift_hour(self.shift)
                over_time = time_difference - shift_hours

                dailyovertime_exists = frappe.db.exists("Daily Over Time", {
                    "date": today,
                    "employee_id": self.employee
                })
                if (over_time > 0.5 and time_difference > shift_hours and not dailyovertime_exists and employee.department=="Production"):
                    # Create Daily Over Time
                    dot = frappe.new_doc("Daily Over Time")
                    dot.employee_id = self.employee
                    dot.check_in_time = first_in_datetime
                    dot.check_out_time = last_out_datetime
                    dot.employee_shift = self.shift
                    dot.shift_hours = shift_hours
                    dot.over_time_hours = over_time
                    dot.check_in_ref = first_in_name
                    dot.check_out_ref = last_out_name
                    dot.save()

                    timesheet_doc = frappe.new_doc("Timesheet")
                    timesheet_doc.employee = self.employee
                    timesheet_detail = timesheet_doc.append("time_logs", {})
                    timesheet_detail.activity_type = "Execution"
                    timesheet_detail.from_time = first_in_datetime
                    timesheet_detail.to_time = last_out_datetime
                    timesheet_detail.checkout_time = last_out_datetime
                    timesheet_detail.hours = over_time
                    timesheet_doc.save()
