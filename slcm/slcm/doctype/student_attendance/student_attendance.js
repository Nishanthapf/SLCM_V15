// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Attendance", {
    student(frm) {
        if (frm.doc.student) {
            // Clear course offer and course to force re-selection
            frm.set_value('course_offer', '');
            frm.set_value('course', '');

            // Fetch enrolled cohorts
            frappe.call({
                method: "slcm.slcm.doctype.student_attendance.student_attendance.get_enrolled_cohorts",
                args: {
                    student: frm.doc.student
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        // Filter Course Offering by these cohorts
                        frm.set_query("course_offer", function () {
                            return {
                                filters: {
                                    cohort: ["in", r.message]
                                }
                            };
                        });
                    } else {
                        // If no enrollments, show empty or all? Default to empty to prevent error
                        frm.set_query("course_offer", function () {
                            return {
                                filters: {
                                    name: ["in", []] // Force empty
                                }
                            };
                        });
                        frappe.msgprint(__("Selected student is not enrolled in any active cohorts."));
                    }
                }
            });
        }
    },

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
