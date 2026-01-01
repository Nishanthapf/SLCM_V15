// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Attendance Tool", {
	setup(frm) {
		frm.students_area = $("<div>").appendTo(frm.fields_dict.students_html.wrapper);
	},

	onload(frm) {
		frm.trigger("set_student_group_query");

		if (!frm.doc.date) {
			frm.set_value("date", frappe.datetime.get_today());
		}
	},

	refresh(frm) {
		if (frappe.route_options) {
			frm.set_value("based_on", frappe.route_options.based_on);
			frm.set_value("student_group", frappe.route_options.student_group);
			frm.set_value("course_schedule", frappe.route_options.course_schedule);
			frappe.route_options = null;
		}

		frm.disable_save();
	},

	/* ---------------- Field Events ---------------- */

	based_on(frm) {
		frm.set_value("student_group", null);
		frm.set_value("group_based_on", null);
		frm.set_value("course_schedule", null);
		frm.students_area.empty();
		frm.trigger("set_student_group_query");
	},

	group_based_on(frm) {
		frm.set_value("student_group", null);
		frm.students_area.empty();
		frm.trigger("set_student_group_query");
	},

	/* ---------------- Link Query (FIXED) ---------------- */

	set_student_group_query(frm) {
		frm.set_query("student_group", () => {
			if (!frm.doc.group_based_on) {
				// Prevent empty dropdown confusion
				return {
					filters: {
						name: ["=", "__invalid__"],
					},
				};
			}

			return {
				filters: {
					group_based_on: frm.doc.group_based_on,
					disabled: 0,
				},
			};
		});
	},

	/* ---------------- Data Fetch ---------------- */

	student_group(frm) {
		if ((frm.doc.student_group && frm.doc.date) || frm.doc.course_schedule) {
			frm.students_area.html(
				"<div style='padding:2rem;text-align:center'>" +
					"<i class='fa fa-spinner fa-spin'></i> Fetching students..." +
					"</div>"
			);

			frappe.call({
				method: "slcm.slcm.doctype.student_attendance_tool.student_attendance_tool.get_student_attendance_records",
				args: {
					based_on: frm.doc.based_on,
					student_group: frm.doc.student_group,
					date: frm.doc.date,
					course_schedule: frm.doc.course_schedule,
				},
				callback(r) {
					frm.events.get_students(frm, r.message || []);
				},
			});
		} else {
			frm.students_area.empty();
		}
	},

	date(frm) {
		if (frm.doc.date > frappe.datetime.get_today()) {
			frappe.throw(__("Cannot mark attendance for future dates."));
		}
		frm.trigger("student_group");
	},

	course_schedule(frm) {
		frm.trigger("student_group");
	},

	get_students(frm, students) {
		frm.students_editor = new StudentsEditor(frm, frm.students_area, students);
	},
});

/* ================= STUDENTS EDITOR ================= */

class StudentsEditor {
	constructor(frm, wrapper, students) {
		this.frm = frm;
		this.wrapper = wrapper;
		this.students = students || [];

		$(this.wrapper).empty();

		if (this.students.length) {
			this.make();
		} else {
			this.show_empty_state();
		}
	}

	make() {
		const me = this;

		const toolbar = $(`
			<div style="margin-bottom:15px">
				<button class="btn btn-default btn-xs btn-check-all">${__("Check all")}</button>
				<button class="btn btn-default btn-xs btn-uncheck-all">${__("Uncheck all")}</button>
				<button class="btn btn-primary btn-xs btn-mark">${__("Mark Attendance")}</button>
				<span class="student-count" style="margin-left:15px;font-weight:bold"></span>
			</div>
		`).appendTo(this.wrapper);

		toolbar.find(".btn-check-all").on("click", () => {
			$(me.wrapper).find("input[type=checkbox]:not(:disabled)").prop("checked", true);
			me.update_count(toolbar);
		});

		toolbar.find(".btn-uncheck-all").on("click", () => {
			$(me.wrapper).find("input[type=checkbox]").prop("checked", false);
			me.update_count(toolbar);
		});

		toolbar.find(".btn-mark").on("click", () => me.mark_attendance(toolbar));

		let html = '<div class="row student-attendance-checks">';
		for (const s of this.students) {
			const checked = s.status === "Present" ? "checked" : "";
			html += `
				<div class="col-sm-3" style="padding:5px">
					<label>
						<input type="checkbox"
							data-student="${s.student}"
							data-name="${s.student_name || s.student}"
							${checked}>
						${s.group_roll_number ? `${s.group_roll_number} - ` : ""}${s.student_name || s.student}
					</label>
				</div>`;
		}
		html += "</div>";

		$(html).appendTo(this.wrapper);

		$(this.wrapper)
			.find("input[type=checkbox]")
			.on("change", () => me.update_count(toolbar));

		this.update_count(toolbar);
	}

	update_count(toolbar) {
		const total = this.students.length;
		const present = $(this.wrapper).find("input[type=checkbox]:checked").length;
		const absent = total - present;

		toolbar
			.find(".student-count")
			.html(__("Total: {0} | Present: {1} | Absent: {2}", [total, present, absent]));
	}

	mark_attendance(toolbar) {
		const students_present = [];
		const students_absent = [];

		$(this.wrapper)
			.find("input[type=checkbox]")
			.each(function () {
				const data = $(this).data();
				const entry = {
					student: data.student,
					student_name: data.name,
				};
				(this.checked ? students_present : students_absent).push(entry);
			});

		frappe.confirm(
			__("Present: {0}<br>Absent: {1}", [students_present.length, students_absent.length]),
			() => {
				frappe.call({
					method: "slcm.api.bulk_attendance.mark_attendance",
					freeze: true,
					args: {
						students_present,
						students_absent,
						student_group: this.frm.doc.student_group,
						course_schedule: this.frm.doc.course_schedule,
						date: this.frm.doc.date,
						based_on: this.frm.doc.based_on,
						group_based_on: this.frm.doc.group_based_on,
					},
					callback: () => {
						frappe.show_alert({
							message: __("Attendance marked"),
							indicator: "green",
						});
						this.frm.trigger("student_group");
					},
				});
			}
		);
	}

	show_empty_state() {
		$(this.wrapper).html(
			`<div class="text-center text-muted" style="padding:2rem">
				${__("No Students found")}
			</div>`
		);
	}
}
