// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Student Attendance", {
// 	refresh(frm) {

// 	},
// });
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
