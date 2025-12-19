// // Copyright (c) 2025, Nishanth and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("Student Enrollment", {
// // 	refresh(frm) {

// // 	},
// // });
// frappe.ui.form.on('Student Enrollment', {

//   program(frm) {

//     // 1️⃣ If program is cleared → clear courses
//     if (!frm.doc.program) {
//       frm.clear_table('table_hxbo');   // Student Enrollment Course
//       frm.refresh_field('table_hxbo');
//       return;
//     }

//     // 2️⃣ Clear existing rows (avoid duplicates)
//     frm.clear_table('courses');

//     // 3️⃣ Fetch Program document with child table
//     frappe.db.get_doc('Program', frm.doc.program)
//       .then(program_doc => {
//         console.log(program_doc, "Response");
//         // 4️⃣ Loop Program → Program Course
//         program_doc.table_fela.forEach(pc => {

//           let row = frm.add_child('table_hxbo'); // Student Enrollment Course

//           row.course = pc.course;
//           row.course_name = pc.course_name;

//         });

//         // 5️⃣ Refresh child table
//         frm.refresh_field('table_hxbo');
//       });
//   }


// });
frappe.ui.form.on('Student Enrollment', {

  program(frm) {

    // 1️⃣ Clear table if program removed
    if (!frm.doc.program) {
      frm.clear_table('table_hxbo');
      frm.refresh_field('table_hxbo');
      return;
    }

    // 2️⃣ Clear existing rows
    frm.clear_table('table_hxbo');

    // 3️⃣ Fetch Program with child table
    frappe.db.get_doc('Program', frm.doc.program).then(program_doc => {

        console.log(program_doc, "Fetched Program");

      if (!program_doc.table_fela || program_doc.table_fela.length === 0) {
        frm.refresh_field('table_hxbo');
        return;
      }

      // 4️⃣ Copy Program Course → Enrollment Course
      program_doc.table_fela.forEach(pc => {

        let row = frm.add_child('table_hxbo');

        // ✅ ALWAYS works
        frappe.model.set_value(row.doctype, row.name, 'course', pc.course);
        frappe.model.set_value(row.doctype, row.name, 'course_name', pc.course_name);

        // ✅ REQUIRED for non-link fields
        frappe.model.set_value(row.doctype, row.name, 'course_type', pc.course_type);
        frappe.model.set_value(row.doctype, row.name, 'course_status', pc.course_status);
        frappe.model.set_value(row.doctype, row.name, 'credit_value', pc.credit_value);

      });

      // 5️⃣ Refresh grid
      frm.refresh_field('table_hxbo');
    });
  }

});
