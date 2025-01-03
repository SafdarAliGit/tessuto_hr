import frappe
from datetime import datetime, timedelta
from frappe.utils import time_diff_in_hours


def shift_hour(shift_type_name):
    shift_duration = 0
    shift = frappe.get_doc('Shift Type', shift_type_name)
    if not shift:
        frappe.throw("Shift Type not found")

    start_time = shift.start_time
    end_time = shift.end_time

    shift_duration = time_diff_in_hours(shift.end_time, shift.start_time)


    if shift_duration <= 0:
        shift_duration = 0

    return shift_duration

