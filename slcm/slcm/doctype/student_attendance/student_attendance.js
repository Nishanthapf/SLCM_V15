// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Attendance", {
    student_group(frm) {
        if (frm.doc.student_group) {
            frappe.db.get_value('Student Group', frm.doc.student_group,
                ['course', 'program', 'academic_year', 'academic_term'], (r) => {
                    if (r && r.course) {
                        // Course Offering is unique per Course, so we fetch by course_title. 
                        // We also check program to be safe, but relax year/term to handle data sync issues.
                        const filters = { 'course_title': r.course };
                        if (r.program) filters['program'] = r.program;

                        frappe.db.get_value('Course Offering', filters, 'name', (data) => {
                            if (data && data.name) {
                                frm.set_value('course_offer', data.name);
                            }
                        });
                    }
                });
        }
    }
});
frappe.listview_settings["Student Attendance"] = {
    onload(listview) {
        $(document).ready(function () {
            $(".filter-x-button").click();
        });

        const style = document.createElement("style");
        style.innerHTML = `
            /* Hide ONLY the heart icon */
            .list-row-like {
                display: none !important;
            }

            /* Hide ONLY the comment icon + count */
            .list-row-activity .comment-count,
            .list-row-activity .comments,
            .list-row-activity .comment-icon,
            .list-row-activity svg.icon-xs {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    },

    refresh(listview) {
        $("span.sidebar-toggle-btn").hide();
        $(".col-lg-2.layout-side-section").hide();
    },
};
