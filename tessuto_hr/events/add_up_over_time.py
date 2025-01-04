import frappe


def before_submit(self, method):
    employee = frappe.db.get_doc("Employee", self.employee)
    employee.custom_over_time = self.custom_over_time if self.custom_over_time else 0
    employee.save()

