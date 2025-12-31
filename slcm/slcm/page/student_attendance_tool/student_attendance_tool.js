// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.pages["student-attendance-tool"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Student Attendance Tool"),
		single_column: true,
	});

	// Add custom CSS for better table display
	$("<style>")
		.prop("type", "text/css")
		.html(
			`
			.student-list-container table tbody {
				display: table-row-group;
			}
			.student-list-container table thead,
			.student-list-container table tbody,
			.student-list-container table tr {
				width: 100%;
				table-layout: fixed;
			}
			.student-list-container table {
				display: table;
				width: 100%;
			}
			.student-row:hover {
				background-color: #f5f5f5;
			}
		`
		)
		.appendTo("head");

	// Initialize the attendance tool
	let attendance_tool = new StudentAttendanceTool(page);
	page.attendance_tool = attendance_tool;
};

class StudentAttendanceTool {
	constructor(page) {
		this.page = page;
		this.students = [];
		this.selected_students = new Set();
		this.init();
	}

	init() {
		this.make_form();
		this.make_student_list();
	}

	make_form() {
		let me = this;

		// Create form container
		this.form_container = $(`
			<div class="attendance-form-container" style="padding: 20px; background: #fff; border-radius: 4px; margin-bottom: 20px;">
				<div class="row">
					<div class="col-md-12">
						<h4>Attendance Configuration</h4>
					</div>
				</div>
				<div class="row" style="margin-top: 15px;">
					<div class="col-md-3">
						<div class="form-group">
							<label>Based On <span class="text-danger">*</span></label>
							<select class="form-control" id="based_on" required>
								<option value="">Select...</option>
								<option value="Student Group">Student Group</option>
								<option value="Course Schedule">Course Schedule</option>
							</select>
						</div>
					</div>
					<div class="col-md-3" id="group_based_on_container" style="display: none;">
						<div class="form-group">
							<label>Group Based On</label>
							<select class="form-control" id="group_based_on">
								<option value="">Select...</option>
								<option value="Batch">Batch</option>
								<option value="Course">Course</option>
								<option value="Activity">Activity</option>
							</select>
						</div>
					</div>
					<div class="col-md-3" id="student_group_container">
						<div class="form-group">
							<label>Student Group <span class="text-danger">*</span></label>
							<div id="student_group_field"></div>
						</div>
					</div>
					<div class="col-md-3" id="course_schedule_container" style="display: none;">
						<div class="form-group">
							<label>Course Schedule <span class="text-danger">*</span></label>
							<div id="course_schedule_field"></div>
						</div>
					</div>
				</div>
				<div class="row" style="margin-top: 15px;">
					<div class="col-md-3">
						<div class="form-group">
							<label>Academic Year</label>
							<div id="academic_year_field"></div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="form-group">
							<label>Academic Term</label>
							<div id="academic_term_field"></div>
						</div>
					</div>
					<div class="col-md-3">
						<div class="form-group">
							<label>Date <span class="text-danger">*</span></label>
							<input type="date" class="form-control" id="attendance_date" required>
						</div>
					</div>
					<div class="col-md-3">
						<div class="form-group">
							<label style="display: block; margin-bottom: 10px;">&nbsp;</label>
							<button class="btn btn-primary" id="get_students_btn" onclick="return false;">
								Get Students
							</button>
						</div>
					</div>
				</div>
			</div>
		`);

		this.page.main.append(this.form_container);

		// Set default date to today
		let today = frappe.datetime.get_today();
		$("#attendance_date").val(today);

		// Initialize link fields
		this.student_group_field = frappe.ui.form.make_control({
			parent: $("#student_group_field"),
			df: {
				fieldtype: "Link",
				fieldname: "student_group",
				options: "Student Group",
				placeholder: "Select Student Group",
				change: () => {
					me.load_student_group_details();
				},
			},
		});
		this.student_group_field.refresh();

		this.course_schedule_field = frappe.ui.form.make_control({
			parent: $("#course_schedule_field"),
			df: {
				fieldtype: "Link",
				fieldname: "course_schedule",
				options: "Course Schedule",
				placeholder: "Select Course Schedule",
				change: () => {
					me.load_course_schedule_details();
				},
			},
		});
		this.course_schedule_field.refresh();

		this.academic_year_field = frappe.ui.form.make_control({
			parent: $("#academic_year_field"),
			df: {
				fieldtype: "Link",
				fieldname: "academic_year",
				options: "Academic Year",
				read_only: 1,
			},
		});
		this.academic_year_field.refresh();

		this.academic_term_field = frappe.ui.form.make_control({
			parent: $("#academic_term_field"),
			df: {
				fieldtype: "Link",
				fieldname: "academic_term",
				options: "Academic Term",
				read_only: 1,
			},
		});
		this.academic_term_field.refresh();

		// Event handlers
		$("#based_on").on("change", function () {
			let based_on = $(this).val();
			if (based_on === "Student Group") {
				$("#group_based_on_container").show();
				$("#student_group_container").show();
				$("#course_schedule_container").hide();
				$("#student_group_field")
					.closest(".form-group")
					.find("label")
					.html('Student Group <span class="text-danger">*</span>');
			} else if (based_on === "Course Schedule") {
				$("#group_based_on_container").hide();
				$("#student_group_container").hide();
				$("#course_schedule_container").show();
				$("#course_schedule_field")
					.closest(".form-group")
					.find("label")
					.html('Course Schedule <span class="text-danger">*</span>');
			} else {
				$("#group_based_on_container").hide();
				$("#student_group_container").hide();
				$("#course_schedule_container").hide();
			}
			me.clear_students();
		});

		$("#get_students_btn").on("click", function () {
			me.get_students();
		});
	}

	load_student_group_details() {
		let me = this;
		let student_group = this.student_group_field.get_value();

		if (!student_group) {
			this.academic_year_field.set_value("");
			this.academic_term_field.set_value("");
			return;
		}

		frappe.db.get_doc("Student Group", student_group).then((doc) => {
			if (doc.academic_year) {
				this.academic_year_field.set_value(doc.academic_year);
			}
			if (doc.academic_term) {
				this.academic_term_field.set_value(doc.academic_term);
			}
		});
	}

	load_course_schedule_details() {
		let me = this;
		let course_schedule = this.course_schedule_field.get_value();

		if (!course_schedule) {
			this.academic_year_field.set_value("");
			this.academic_term_field.set_value("");
			return;
		}

		frappe.db.get_doc("Course Schedule", course_schedule).then((doc) => {
			if (doc.student_group) {
				frappe.db.get_doc("Student Group", doc.student_group).then((group_doc) => {
					if (group_doc.academic_year) {
						this.academic_year_field.set_value(group_doc.academic_year);
					}
					if (group_doc.academic_term) {
						this.academic_term_field.set_value(group_doc.academic_term);
					}
				});
			}
		});
	}

	make_student_list() {
		let me = this;

		this.student_list_container = $(`
			<div class="student-list-container" style="padding: 20px; background: #fff; border-radius: 4px;">
				<div class="row">
					<div class="col-md-12">
						<h4>Bulk Attendance Marking</h4>
					</div>
				</div>
				<div class="row" style="margin-top: 15px; margin-bottom: 15px;">
					<div class="col-md-12">
						<div class="alert alert-info" id="student_stats" style="display: none; padding: 10px 15px;">
							<strong>Total Students:</strong> <span id="total_count">0</span> |
							<strong>Selected (Present):</strong> <span id="selected_count" style="color: green; font-weight: bold;">0</span> |
							<strong>Unselected (Absent):</strong> <span id="unselected_count" style="color: red; font-weight: bold;">0</span>
						</div>
					</div>
				</div>
				<div class="row" style="margin-top: 15px; margin-bottom: 15px;">
					<div class="col-md-12">
						<button class="btn btn-sm btn-success" id="check_all_btn">
							<i class="fa fa-check-square"></i> Check All (Mark All Present)
						</button>
						<button class="btn btn-sm btn-warning" id="uncheck_all_btn" style="margin-left: 5px;">
							<i class="fa fa-square"></i> Uncheck All (Mark All Absent)
						</button>
						<button class="btn btn-sm btn-primary" id="mark_attendance_btn" style="margin-left: 10px;">
							<i class="fa fa-save"></i> Mark Attendance for All Students
						</button>
						<span id="attendance_status" style="margin-left: 15px; font-weight: bold;"></span>
					</div>
				</div>
				<div class="row">
					<div class="col-md-12">
						<div style="border: 1px solid #ddd; border-radius: 4px; overflow: hidden; max-height: 600px; overflow-y: auto;">
							<table class="table table-bordered table-hover" style="margin-bottom: 0; table-layout: fixed;">
								<thead style="background-color: #f5f5f5; position: sticky; top: 0; z-index: 10;">
									<tr>
										<th style="width: 50px; text-align: center;">
											<input type="checkbox" id="select_all_checkbox" title="Select All">
										</th>
										<th style="width: 60px;">S.No</th>
										<th>Student ID</th>
										<th>Student Name</th>
										<th style="width: 100px; text-align: center;">Roll No</th>
										<th style="width: 120px; text-align: center;">Status</th>
									</tr>
								</thead>
								<tbody id="students_list">
									<tr>
										<td colspan="6" class="text-center text-muted" style="padding: 40px;">
											Select configuration above and click "Get Students" to load student list
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</div>
			</div>
		`);

		this.page.main.append(this.student_list_container);

		$("#check_all_btn").on("click", function () {
			me.check_all();
		});

		$("#uncheck_all_btn").on("click", function () {
			me.uncheck_all();
		});

		$("#mark_attendance_btn").on("click", function () {
			me.mark_attendance();
		});

		$("#select_all_checkbox").on("change", function () {
			if ($(this).is(":checked")) {
				me.check_all();
			} else {
				me.uncheck_all();
			}
		});
	}

	get_students() {
		let me = this;
		let based_on = $("#based_on").val();
		let attendance_date = $("#attendance_date").val();

		if (!based_on) {
			frappe.msgprint(__("Please select 'Based On'"));
			return;
		}

		if (!attendance_date) {
			frappe.msgprint(__("Please select Date"));
			return;
		}

		if (based_on === "Student Group") {
			let student_group = this.student_group_field.get_value();
			if (!student_group) {
				frappe.msgprint(__("Please select Student Group"));
				return;
			}
			this.get_students_from_group(student_group, attendance_date);
		} else if (based_on === "Course Schedule") {
			let course_schedule = this.course_schedule_field.get_value();
			if (!course_schedule) {
				frappe.msgprint(__("Please select Course Schedule"));
				return;
			}
			this.get_students_from_schedule(course_schedule, attendance_date);
		}
	}

	get_students_from_group(student_group, attendance_date) {
		let me = this;

		frappe.call({
			method: "slcm.api.bulk_attendance.get_students_from_group",
			args: {
				student_group: student_group,
				attendance_date: attendance_date,
			},
			callback: function (r) {
				if (r.message) {
					me.students = r.message;
					me.render_student_list();
				}
			},
		});
	}

	get_students_from_schedule(course_schedule, attendance_date) {
		let me = this;

		frappe.call({
			method: "slcm.api.bulk_attendance.get_students_from_schedule",
			args: {
				course_schedule: course_schedule,
			},
			callback: function (r) {
				if (r.message) {
					me.students = r.message;
					me.render_student_list();
				}
			},
		});
	}

	render_student_list() {
		let me = this;
		let html = "";

		if (!this.students || this.students.length === 0) {
			html = `
				<tr>
					<td colspan="6" class="text-center text-muted" style="padding: 40px;">
						No students found
					</td>
				</tr>
			`;
		} else {
			// By default, mark all as present (checked)
			this.selected_students.clear();
			this.students.forEach((student) => {
				this.selected_students.add(student.student);
			});

			this.students.forEach((student, index) => {
				let is_checked = this.selected_students.has(student.student);
				let status_badge = is_checked
					? '<span class="badge badge-success">Present</span>'
					: '<span class="badge badge-danger">Absent</span>';

				html += `
					<tr class="student-row" data-student="${student.student}">
						<td style="text-align: center;">
							<input type="checkbox"
								class="student-checkbox"
								data-student="${student.student}"
								${is_checked ? "checked" : ""}>
						</td>
						<td>${index + 1}</td>
						<td><strong>${student.student}</strong></td>
						<td>${student.student_name || student.student}</td>
						<td style="text-align: center;">${student.group_roll_number || "-"}</td>
						<td class="status-cell" style="text-align: center;">${status_badge}</td>
					</tr>
				`;
			});
		}

		$("#students_list").html(html);
		this.update_statistics();

		// Attach checkbox event handlers
		$(".student-checkbox").on("change", function () {
			let student = $(this).data("student");
			let row = $(this).closest("tr");
			let statusCell = row.find(".status-cell");

			if ($(this).is(":checked")) {
				me.selected_students.add(student);
				statusCell.html('<span class="badge badge-success">Present</span>');
			} else {
				me.selected_students.delete(student);
				statusCell.html('<span class="badge badge-danger">Absent</span>');
			}
			me.update_statistics();
			me.update_select_all_checkbox();
		});
	}

	update_statistics() {
		let total = this.students.length;
		let selected = this.selected_students.size;
		let unselected = total - selected;

		$("#total_count").text(total);
		$("#selected_count").text(selected);
		$("#unselected_count").text(unselected);

		if (total > 0) {
			$("#student_stats").show();
		} else {
			$("#student_stats").hide();
		}

		// Update button text
		if (total > 0) {
			$("#mark_attendance_btn").html(
				`<i class="fa fa-save"></i> Mark Attendance for All ${total} Students`
			);
		}
	}

	update_select_all_checkbox() {
		let total = this.students.length;
		let selected = this.selected_students.size;

		if (selected === total && total > 0) {
			$("#select_all_checkbox").prop("checked", true);
		} else {
			$("#select_all_checkbox").prop("checked", false);
		}
	}

	check_all() {
		this.selected_students.clear();
		this.students.forEach((student) => {
			this.selected_students.add(student.student);
		});
		$(".student-checkbox").prop("checked", true);
		$(".status-cell").html('<span class="badge badge-success">Present</span>');
		$("#select_all_checkbox").prop("checked", true);
		this.update_statistics();
	}

	uncheck_all() {
		this.selected_students.clear();
		$(".student-checkbox").prop("checked", false);
		$(".status-cell").html('<span class="badge badge-danger">Absent</span>');
		$("#select_all_checkbox").prop("checked", false);
		this.update_statistics();
	}

	mark_attendance() {
		let me = this;
		let based_on = $("#based_on").val();
		let attendance_date = $("#attendance_date").val();

		if (!attendance_date) {
			frappe.msgprint(__("Please select Date"));
			return;
		}

		if (this.students.length === 0) {
			frappe.msgprint(__("No students to mark attendance for"));
			return;
		}

		// Prepare attendance data - mark ALL students
		let attendance_data = {};
		let present_count = 0;
		let absent_count = 0;

		this.students.forEach((student) => {
			if (this.selected_students.has(student.student)) {
				attendance_data[student.student] = "Present";
				present_count++;
			} else {
				attendance_data[student.student] = "Absent";
				absent_count++;
			}
		});

		let confirm_message = __(
			"Mark attendance for all {0} students?<br><br>" +
				"<strong>Present:</strong> {1} students<br>" +
				"<strong>Absent:</strong> {2} students",
			[this.students.length, present_count, absent_count]
		);

		frappe.confirm(
			confirm_message,
			function () {
				// Yes
				$("#attendance_status").html(
					'<span class="text-info"><i class="fa fa-spinner fa-spin"></i> Processing...</span>'
				);

				if (based_on === "Student Group") {
					let student_group = me.student_group_field.get_value();
					me.create_bulk_attendance_from_group(
						student_group,
						attendance_date,
						attendance_data
					);
				} else if (based_on === "Course Schedule") {
					let course_schedule = me.course_schedule_field.get_value();
					me.create_bulk_attendance_from_schedule(
						course_schedule,
						attendance_date,
						attendance_data
					);
				}
			},
			function () {
				// No
			}
		);
	}

	create_bulk_attendance_from_group(student_group, attendance_date, attendance_data) {
		let me = this;

		frappe.call({
			method: "slcm.api.bulk_attendance.create_bulk_attendance_from_group",
			args: {
				student_group: student_group,
				attendance_date: attendance_date,
				attendance_data: attendance_data,
			},
			freeze: true,
			freeze_message: __("Marking attendance for all students..."),
			callback: function (r) {
				if (r.message) {
					let msg = r.message.message || "Attendance marked successfully";
					let details = "";
					if (r.message.total_processed) {
						details = `<br><strong>Total Processed:</strong> ${r.message.total_processed} students`;
						if (r.message.created > 0) {
							details += ` | <strong>Created:</strong> ${r.message.created}`;
						}
						if (r.message.updated > 0) {
							details += ` | <strong>Updated:</strong> ${r.message.updated}`;
						}
					}

					frappe.show_alert(
						{
							message: msg + details,
							indicator: "green",
						},
						8
					);

					$("#attendance_status").html(
						`<span class="text-success"><i class="fa fa-check-circle"></i> ${msg}</span>`
					);

					// Don't clear students, allow for review
					setTimeout(() => {
						$("#attendance_status").html("");
					}, 8000);
				}
			},
		});
	}

	create_bulk_attendance_from_schedule(course_schedule, attendance_date, attendance_data) {
		let me = this;

		frappe.call({
			method: "slcm.api.bulk_attendance.create_bulk_attendance_from_schedule",
			args: {
				course_schedule: course_schedule,
				attendance_date: attendance_date,
				attendance_data: attendance_data,
			},
			freeze: true,
			freeze_message: __("Marking attendance for all students..."),
			callback: function (r) {
				if (r.message) {
					let msg = r.message.message || "Attendance marked successfully";
					let details = "";
					if (r.message.total_processed) {
						details = `<br><strong>Total Processed:</strong> ${r.message.total_processed} students`;
						if (r.message.created > 0) {
							details += ` | <strong>Created:</strong> ${r.message.created}`;
						}
						if (r.message.updated > 0) {
							details += ` | <strong>Updated:</strong> ${r.message.updated}`;
						}
					}

					frappe.show_alert(
						{
							message: msg + details,
							indicator: "green",
						},
						8
					);

					$("#attendance_status").html(
						`<span class="text-success"><i class="fa fa-check-circle"></i> ${msg}</span>`
					);

					// Don't clear students, allow for review
					setTimeout(() => {
						$("#attendance_status").html("");
					}, 8000);
				}
			},
		});
	}

	clear_students() {
		this.students = [];
		this.selected_students.clear();
		$("#students_list").html(
			'<tr><td colspan="6" class="text-center text-muted" style="padding: 40px;">Select configuration above and click "Get Students" to load student list</td></tr>'
		);
		$("#student_stats").hide();
		$("#attendance_status").html("");
	}
}
