import frappe

def custom_validate(self, method):
    ctc_percent = frappe.db.get_single_value("Employee Advance Setting", "ctc_percent")
    ctc = self.custom_ctc * (ctc_percent / 100)
    if self.advance_amount > ctc:
        frappe.throw("❌ The advance amount cannot be greater than {ctc_percent}% of CTC.")
    
