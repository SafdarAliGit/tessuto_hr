import frappe


def submit(self, method):
    current_total = frappe.db.get_value("Employee", self.employee, "total_over_time") or 0
    new_total = current_total + (self.total_hours or 0)
    frappe.db.set_value("Employee", self.employee, "total_over_time", new_total)
