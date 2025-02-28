import frappe

def custom_validate(self, method):
    if self.advance_amount > self.custom_ctc/2:
        frappe.throw("❌ The advance amount cannot be greater than 50% of CTC.")
    
