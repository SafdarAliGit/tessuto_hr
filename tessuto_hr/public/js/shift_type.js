frappe.ui.form.on('Shift Type', {
    refresh: function (frm) {
        // Add custom button
        frm.add_custom_button('Create Timesheet For DOT', function () {
            // Call the server-side function
            frappe.call({
                method: "tessuto_hr.events.create_timesheet.create_timesheet",
                args: {
                    attendance_name: frm.doc.name
                },
                callback: function (response) {
                    // Log the response to the console
                    console.log(response.message);
                }
            });
        });
    }
});
