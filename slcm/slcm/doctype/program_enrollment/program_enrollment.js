// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Program Enrollment", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Program Enrollment', {

  program(frm) {

    // 1️⃣ If program is cleared → clear courses
    if (!frm.doc.program) {
      frm.clear_table('table_hxbo');   // Program Enrollment Course
      frm.refresh_field('table_hxbo');
      return;
    }

    // 2️⃣ Clear existing rows (avoid duplicates)
    frm.clear_table('courses');

    // 3️⃣ Fetch Program document with child table
    frappe.db.get_doc('Program', frm.doc.program)
      .then(program_doc => {
        console.log(program_doc, "Response");
        // 4️⃣ Loop Program → Program Course
        program_doc.table_fela.forEach(pc => {

          let row = frm.add_child('table_hxbo'); // Program Enrollment Course

          row.course = pc.course;
          row.course_name = pc.course_name;

        });

        // 5️⃣ Refresh child table
        frm.refresh_field('table_hxbo');
      });
  }


});
