from hrms.hr.doctype.attendance.attendance import Attendance
import frappe
from datetime import datetime


class AttendanceOverride(Attendance):
    def before_save(self):
        # Get the current year and month
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        # Query to count late entries for the current month for the given employee
        count = frappe.db.count('Attendance', filters={
            'attendance_date': ['like', f'{current_year}-{current_month:02d}%'],  # Match year-month
            'employee': self.employee,
            'late_entry': 1  # Only count late entries
        })

        # Update the custom late entry count field
        if self.late_entry == 1:
            count +=1
            self.custom_late_entry_count = count
        self.custom_late_entry_count = count

        # Check if count is a multiple of 3 (e.g., 3, 6, 9, etc.)
        if count > 0 and count % 3 == 0:
            self.status = "Absent"
