// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.ui.form.on("Curriculum Management", {
	refresh: function (frm) {
		frm.disable_save();

		// -------------------------------------------------------------------------
		// AGGRESSIVE SAVE OVERRIDE to prevent LinkValidationError on Single DocType
		// -------------------------------------------------------------------------

		// 1. Override the form instance save method
		frm.save = function () {
			if (frm.doc.program && frm.doc.academic_year && frm.doc.department) {
				frm.trigger("save_curriculum");
			} else {
				frappe.msgprint(__("Please select Program, Academic Year and Department first."));
			}
			return Promise.resolve(); // Fake promise to satisfy callers
		};

		// 2. Override the primary action explicitly
		frm.page.set_primary_action("Save", function () {
			frm.save();
		});

		// 3. Hijack the Ctrl+S shortcut explicitly for this page
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+s",
			action: function () {
				frm.save();
				return false; // Prevent default
			},
			description: __("Save Curriculum"),
			page: frm.page,
		});

		// Load UI if data already present
		if (frm.doc.department && frm.doc.program && frm.doc.academic_year) {
			frm.trigger("autorefresh");
		}

		frm.add_custom_button(__("Reset Filters"), function () {
			frm.set_value("department", "");
			frm.set_value("program", "");
			frm.set_value("academic_year", "");
			frm.set_value("batch", "");
			frm.set_value("section", "");
			frm.curriculum_data = null;
			frm.trigger("render_ui");
		});
	},

	onload: function (frm) {
		// Pre-load Course metadata for dynamic rendering
		frappe.model.with_doctype("Course", () => {
			// Metadata loaded
		});

		if (frm.is_new()) {
			frm.trigger("set_defaults");
		}
	},

	set_defaults: function (frm) {
		// Handled by python onload
	},

	department: function (frm) {
		frm.trigger("autorefresh");
	},

	program: function (frm) {
		frm.trigger("autorefresh");
	},

	academic_year: function (frm) {
		if (frm.doc.academic_year) {
			frappe.db
				.get_value("Academic Year", frm.doc.academic_year, "academic_system")
				.then((r) => {
					if (r.message && r.message.academic_system) {
						frm.set_value("academic_system", r.message.academic_system).then(() => {
							frm.trigger("autorefresh");
						});
					} else {
						frm.trigger("autorefresh");
					}
				});
		} else {
			frm.trigger("autorefresh");
		}
	},

	academic_system: function (frm) {
		frm.term_list = null; // Reset on system change
		frm.trigger("render_ui");
	},

	autorefresh: function (frm) {
		frm.trigger("load_curriculum");
	},

	batch: function (frm) {
		if (frm.doc.batch) {
			frm.set_query("section", function () {
				return {
					filters: {
						batch: frm.doc.batch,
					},
				};
			});
		}
	},

	section: function (frm) {
		if (frm.doc.section) {
			frappe.call({
				method: "slcm.slcm.doctype.curriculum_management.curriculum_management.get_details_from_section",
				args: { section: frm.doc.section },
				callback: function (r) {
					if (r.message) {
						// Set values sequentially to allow triggers to check completeness
						// We use promises explicitly to ensure order if needed, but standard set_value is enough
						// as the 'autorefresh' check requires ALL fields.
						if (r.message.department) frm.set_value("department", r.message.department);
						if (r.message.program) frm.set_value("program", r.message.program);
						if (r.message.academic_year) frm.set_value("academic_year", r.message.academic_year);
						if (r.message.batch && r.message.batch !== frm.doc.batch) {
							frm.set_value("batch", r.message.batch);
						}
					}
				},
			});
		}
	},

	load_curriculum: function (frm) {
		if (frm.doc.department && frm.doc.program && frm.doc.academic_year) {
			frappe.call({
				method: "slcm.slcm.doctype.curriculum_management.curriculum_management.get_curriculum",
				args: {
					program: frm.doc.program,
					academic_year: frm.doc.academic_year,
					batch: frm.doc.batch,   // Added
					section: frm.doc.section // Added
				},
				callback: function (r) {
					if (r.message) {
						frm.curriculum_data = r.message;
						frm.term_list = null; // Reset logic on load

						// Sync system logic
						if (r.message.academic_system) {
							if (frm.doc.academic_system !== r.message.academic_system) {
								frm.set_value("academic_system", r.message.academic_system).then(
									() => {
										frm.trigger("render_ui");
									}
								);
								return; // Don't render twice
							}
						}

						frm.trigger("render_ui");
					}
				},
			});
		} else {
			$(frm.fields_dict.ui_container.wrapper).html(
				'<div class="text-muted text-center p-5">Please select Department, Program, Academic Year (and optional Batch)</div>'
			);
		}
	},

	render_ui: function (frm) {
		// Ensure metadata is available before rendering
		frappe.model.with_doctype("Course", () => {
			frm.trigger("_render_ui_internal");
		});
	},

	_render_ui_internal: function (frm) {
		const wrapper = $(frm.fields_dict.ui_container.wrapper);
		const activeTermId = wrapper.find(".collapse.show").attr("id");
		wrapper.empty();

		if (!frm.curriculum_data) return;

		// Get Dynamic Columns from Course Meta
		const course_meta = frappe.get_meta("Course");
		const course_fields = course_meta.fields.filter((df) => {
			return (
				df.in_list_view &&
				!df.hidden &&
				!["Section Break", "Column Break", "HTML", "Table", "Button"].includes(
					df.fieldtype
				)
			);
		});

		const enrollment_types = (frm.doc.enrollment_types || []).filter((d) => d.is_active);
		const system = frm.doc.academic_system || "Semester";

		let defaultCount = 8;
		if (system === "Trimester") defaultCount = 3;
		else if (system === "Quarter") defaultCount = 4;
		else if (system === "Year") defaultCount = 5;

		// Re-calculate term list based on current data state
		// Use a Set to track all active terms
		// Initialize with existing term_list to preserve manual additions
		let activeTerms = new Set(frm.term_list || []);
		for (let i = 1; i <= defaultCount; i++) activeTerms.add(i);

		(frm.curriculum_data.curriculum_courses || []).forEach((c) => {
			if (c.semester && c.semester.startsWith(system)) {
				const parts = c.semester.split(" ");
				if (parts.length > 1) {
					const num = parseInt(parts[1]);
					if (!isNaN(num)) activeTerms.add(num);
				}
			}
		});
		frm.term_list = Array.from(activeTerms).sort((a, b) => a - b);

		// Render Container
		const html = `
            <div class="curriculum-manager">
                <div class="clearfix mb-3">
                    <div class="text-muted small float-left">
                        Configure courses for ${frm.curriculum_data.program} (${frm.curriculum_data.academic_year}) - <b>${system} System</b>
                    </div>
                </div>

                <div class="card mb-3">
                    <div class="card-header">
                        <h5 class="mb-0">Term Dependent Curriculum</h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="accordion" id="accordionSemesters"></div>
                    </div>
                    <div class="card-footer p-2 text-center">
                        <button class="btn btn-sm btn-default btn-add-term">+ Add ${system}</button>
                        <button class="btn btn-sm btn-danger btn-remove-terms ml-2">- Remove ${system}</button>
                    </div>
                </div>
            </div>
        `;

		const $container = $(html).appendTo(wrapper);
		const $accordion = $container.find("#accordionSemesters");

		frm.term_list.forEach((term) => {
			const termName = `${system} ${term}`;
			const coursesInSem = (frm.curriculum_data.curriculum_courses || []).filter(
				(c) => c.semester === termName
			);

			const termId = `collapse${term}`;
			const isVisible =
				(frm.active_term_name && frm.active_term_name === termName) ||
				(!frm.active_term_name && activeTermId === termId);
			const showClass = isVisible ? "show" : "";

			const semHtml = `
                <div class="card">
                    <div class="card-header" id="heading${term}">
                        <h2 class="mb-0">
                            <button class="btn btn-link btn-block text-left collapsed" type="button" data-toggle="collapse" data-target="#collapse${term}">
                                ${termName}
                            </button>
                        </h2>
                    </div>

                    <div id="collapse${term}" class="collapse ${showClass}" data-parent="#accordionSemesters">
                        <div class="card-body">
                            <div class="enrollment-types-container-${term}"></div>
                        </div>
                    </div>
                </div>
            `;

			const $semBlock = $(semHtml).appendTo($accordion);
			const $etContainer = $semBlock.find(`.enrollment-types-container-${term}`);

			enrollment_types.forEach((et) => {
				const etCourses = coursesInSem.filter(
					(c) => c.enrollment_type === et.enrollment_type
				);

				const etHtml = `
                    <div class="enrollment-section mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="font-weight-bold text-dark" style="text-transform: uppercase; font-size: 13px; letter-spacing: 0.5px;">
                                ${et.display_name || et.enrollment_type}
                            </h6>
                            <div>
                                <button class="btn btn-xs btn-default btn-add-course"
                                    data-sem="${termName}" data-et="${et.enrollment_type
					}">+ Add Course</button>
                                ${et.enrollment_type !== "Core"
						? `<button class="btn btn-xs btn-default btn-add-cluster ml-1"
                                            data-sem="${termName}" data-et="${et.enrollment_type}">+ Add Cluster</button>`
						: ""
					}
                            </div>
                        </div>
                        <div class="list-group">
                            ${etCourses
						.map((course, idx) =>
							render_course_item(
								course,
								idx,
								termName,
								et.enrollment_type,
								course_fields
							)
						)
						.join("")}
                        </div>
                    </div>
                `;
				$etContainer.append(etHtml);
			});
		});

		if (frm.active_term_name) delete frm.active_term_name;

		// Bind Events
		$container.find(".btn-add-course").on("click", function (e) {
			e.preventDefault();
			add_course_dialog(frm, $(this).data("sem"), $(this).data("et"), course_fields);
		});

		$container.find(".btn-add-cluster").on("click", function (e) {
			e.preventDefault();
			add_cluster_dialog(frm, $(this).data("sem"), $(this).data("et"));
		});

		$container.find(".btn-add-term").on("click", function (e) {
			e.preventDefault();
			const max = frm.term_list.length > 0 ? Math.max(...frm.term_list) : 0;
			frm.term_list.push(max + 1);
			// We don't save just by adding a term visually, but we render
			frm.trigger("render_ui");
		});

		$container.find(".btn-remove-terms").on("click", function (e) {
			e.preventDefault();
			remove_term_dialog(frm, system, defaultCount);
		});

		// Delegation for Edit/Remove
		$container.on("click", ".edit-course", function (e) {
			e.preventDefault();
			const $btn = $(this);
			// Identify item by data attributes
			const item = find_item_by_data(frm, $btn);
			if (item) {
				if (item.course_group_type === "Cluster") edit_cluster_dialog(frm, item);
				else edit_course_dialog(frm, item, course_fields);
			}
		});

		$container.on("click", ".remove-course", function (e) {
			e.preventDefault();
			remove_item(frm, $(this));
		});
	},

	save_curriculum: function (frm) {
		if (!frm.curriculum_data || !frm.doc.department) {
			frappe.msgprint("Please select a Department");
			return;
		}

		frappe.call({
			method: "slcm.slcm.doctype.curriculum_management.curriculum_management.save_curriculum",
			args: {
				program: frm.doc.program,
				academic_year: frm.doc.academic_year,
				department: frm.doc.department,
				academic_system: frm.doc.academic_system,
				batch: frm.doc.batch,       // Added
				section: frm.doc.section,   // Added
				courses: JSON.stringify(frm.curriculum_data.curriculum_courses || []),
			},
			freeze: true,
			callback: function (r) {
				frappe.show_alert({
					message: __("Curriculum Saved Successfully"),
					indicator: "green",
				});
				frm.trigger("autorefresh");
			},
		});
	},
});

// -----------------------------------------------------------------------------
// HELPER FUNCTIONS
// -----------------------------------------------------------------------------

function find_item_by_data(frm, $el) {
	const sem = $el.data("sem");
	const et = $el.data("et");
	const courseName = $el.data("course");
	const clusterName = $el.data("cluster");
	const isCluster = !!clusterName;

	return (frm.curriculum_data.curriculum_courses || []).find((c) => {
		if (c.semester === sem && c.enrollment_type === et) {
			if (isCluster) {
				return c.course_group_type === "Cluster" && c.cluster_name === clusterName;
			} else {
				return c.course_group_type === "Course" && c.course === courseName;
			}
		}
		return false;
	});
}

function remove_item(frm, $el) {
	const sem = $el.data("sem");
	const et = $el.data("et");
	const courseName = $el.data("course");
	const clusterName = $el.data("cluster");
	const isCluster = !!clusterName;

	// Find item first to get details for message
	const itemToRemove = find_item_by_data(frm, $el);
	if (!itemToRemove) return;

	let confirmMsg = "";
	if (isCluster) {
		confirmMsg = __("Are you sure you want to remove cluster <b>{0}</b>?", [clusterName]);
	} else {
		const codeStr = itemToRemove.course_code ? ` (${itemToRemove.course_code})` : "";
		confirmMsg = __("Are you sure you want to remove course <b>{0}</b>{1}?", [courseName, codeStr]);
	}

	frappe.confirm(confirmMsg, () => {
		let deleted = false;
		frm.curriculum_data.curriculum_courses = (frm.curriculum_data.curriculum_courses || []).filter(
			(c) => {
				if (deleted) return true; // delete only first match
				if (c.semester === sem && c.enrollment_type === et) {
					if (isCluster) {
						if (c.course_group_type === "Cluster" && c.cluster_name === clusterName) {
							deleted = true;
							return false;
						}
					} else {
						if (c.course_group_type === "Course" && c.course === courseName) {
							deleted = true;
							return false;
						}
					}
				}
				return true;
			}
		);

		frm.active_term_name = sem;
		// IMMEDIATE UPDATE
		frm.trigger("render_ui");
		// BACKGROUND SAVE
		frm.trigger("save_curriculum");
	});
}

function render_course_item(course, idx, resultSem, resultEt, course_fields) {
	if (course.course_group_type === "Cluster") {
		return `
            <div class="list-group-item p-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${course.cluster_name}</strong> <span class="badge badge-info ml-1">Cluster</span><br>
                        <small class="text-muted">Min: ${course.min_courses}, Max: ${course.max_courses}</small>
                    </div>
                    <div>
                        <button class="btn btn-xs text-danger remove-course"
                            data-sem="${resultSem}" data-et="${resultEt}" data-cluster="${course.cluster_name}">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
	} else {
		// DYNAMIC FIELD RENDERING
		// We want to show "credits" specifically, but also any other interesting field
		// For the compact view, let's stick to Name + Credits + maybe Code or Type
		// But the "Edit" dialog MUST be fully dynamic.

		// Let's create a small info string for the secondary line
		let infoParts = [];
		// Always show credits as it's critical
		infoParts.push(`Credits: ${course.credits || course.credit_value || 0}`);

		// Add other fields if they have value (optional, keep it clean)
		course_fields.forEach((f) => {
			if (
				f.fieldname !== "course_name" &&
				f.fieldname !== "credit_value" &&
				course[f.fieldname]
			) {
				// skip internal fields
				infoParts.push(`${f.label}: ${course[f.fieldname]}`);
			}
		});

		// Limit info to avoid bloating UI
		// Actually, let's stick to Credits + Code if available

		return `
            <div class="list-group-item p-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${course.course}</strong><br>
                        <small class="text-muted">${infoParts.join(" | ")}</small>
                    </div>
                    <div>
                        <button class="btn btn-xs text-danger remove-course"
                            data-sem="${resultSem}" data-et="${resultEt}" data-course="${course.course
			}">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
	}
}

function remove_term_dialog(frm, system, defaultCount) {
	const d = new frappe.ui.Dialog({
		title: `Remove ${system}s`,
		fields: [
			{
				fieldtype: "MultiCheck",
				label: "Select Terms to Remove",
				fieldname: "terms",
				options: frm.term_list.map((t) => ({
					label: `${system} ${t}`,
					value: t,
				})),
				columns: 2,
			},
		],
		primary_action_label: "Remove Selected",
		primary_action: (values) => {
			const toRemove = values.terms || [];
			if (toRemove.length === 0) return;

			// Check restrictions
			const restricted = toRemove.filter((t) => t <= defaultCount);
			if (restricted.length > 0) {
				frappe.msgprint({
					title: __("Cannot Remove Defaults"),
					message: __(
						`Cannot remove default ${system}s: <b>${restricted.join(", ")}</b>`
					),
					indicator: "orange",
				});
				return;
			}

			const removeNames = toRemove.map((t) => `${system} ${t}`);
			if (frm.curriculum_data.curriculum_courses) {
				frm.curriculum_data.curriculum_courses =
					frm.curriculum_data.curriculum_courses.filter(
						(c) => !removeNames.includes(c.semester)
					);
			}

			frm.term_list = frm.term_list.filter((t) => !toRemove.includes(t));
			frm.trigger("render_ui");
			frm.trigger("save_curriculum");
			d.hide();
		},
	});
	d.show();
}

function add_course_dialog(frm, semester, enrollment_type) {
	let selected = new Set();

	const d = new frappe.ui.Dialog({
		title: "Select Courses",
		size: "extra-large",
		fields: [
			{
				fieldtype: "Data",
				fieldname: "search",
				label: "Search",
				onchange() {
					load_courses();
				},
			},
			{
				fieldtype: "Link",
				fieldname: "department",
				label: "Department",
				options: "Department",
				default: frm.doc.department,
				onchange() {
					load_courses();
				},
			},
			{
				fieldtype: "HTML",
				fieldname: "course_table",
			},
		],
		primary_action_label: "Add Selected Courses",
		primary_action() {
			if (!frm.curriculum_data.curriculum_courses) {
				frm.curriculum_data.curriculum_courses = [];
			}

			let added = 0;

			selected.forEach((c) => {
				const exists = frm.curriculum_data.curriculum_courses.find(
					(e) =>
						e.semester === semester &&
						e.enrollment_type === enrollment_type &&
						e.course_group_type === "Course" &&
						e.course === c.name
				);

				if (exists) return;

				frm.curriculum_data.curriculum_courses.push({
					semester: semester,
					enrollment_type: enrollment_type,
					course_group_type: "Course",
					course: c.name,
					course_code: c.course_code,
					credits: c.credit_value,
					department_name: c.department_name,
				});

				added++;
			});

			if (added > 0) {
				frm.active_term_name = semester;
				frm.trigger("render_ui");
				frm.trigger("save_curriculum");
			}

			d.hide();
		},
	});

	d.show();

	function load_courses() {
		const values = d.get_values() || {};
		const filters = {
			status: "Active",
		};

		if (values.department) filters.department = values.department;
		if (values.search) {
			filters.course_name = ["like", `%${values.search}%`];
		}

		frappe.db
			.get_list("Course", {
				fields: [
					"name",
					"course_name",
					"course_code",
					"department",
					"department_name",
					"credit_value",
					"status",
				],
				filters: filters,
				limit: 100,
			})
			.then((rows) => {
				render_table(rows);
			});
	}

	function render_table(rows) {
		const wrapper = d.fields_dict.course_table.$wrapper;
		wrapper.empty();

		const table = $(`
			<table class="table table-bordered table-hover">
				<thead>
					<tr>
						<th style="width:40px; text-align: center;"><input type="checkbox" class="select-all"></th>
						<th>Course Name</th>
						<th>Course Code</th>
						<th>Department</th>
						<th>Credits</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody></tbody>
			</table>
		`);

		const tbody = table.find("tbody");
		const selectAll = table.find(".select-all");

		// Check already existing courses in this semester
		const existingCourses = new Set();
		if (frm.curriculum_data.curriculum_courses) {
			frm.curriculum_data.curriculum_courses.forEach(c => {
				if (c.semester === semester && c.course_group_type === "Course") {
					existingCourses.add(c.course);
				}
			});
		}

		// Filter out rows that are already added (for master checkbox logic)
		const selectableRows = rows.filter(r => !existingCourses.has(r.name));

		// Check if all selectable rows are currently selected
		const allSelected = selectableRows.length > 0 && selectableRows.every(r => selected.has(r.name));
		selectAll.prop("checked", allSelected);

		// If no rows are selectable, disable master checkbox
		if (selectableRows.length === 0) {
			selectAll.prop("disabled", true);
		}

		selectAll.on("change", function () {
			const isChecked = $(this).prop("checked");

			selectableRows.forEach(r => {
				// Only toggle valid rows
				const $checkbox = tbody.find(`input[data-name='${r.name}']`);
				$checkbox.prop("checked", isChecked);

				if (isChecked) selected.add(r);
				else selected.delete(r);
			});
		});

		rows.forEach((r) => {
			const isAlreadyAdded = existingCourses.has(r.name);
			const checked = selected.has(r.name) ? "checked" : "";
			const disabled = isAlreadyAdded ? "disabled" : "";

			let statusHtml = r.status;
			if (isAlreadyAdded) {
				statusHtml = `<span class="text-muted">Already Added</span>`;
			}

			const tr = $(`
				<tr class="${isAlreadyAdded ? 'text-muted' : ''}" style="${isAlreadyAdded ? 'background-color: #f8f9fa;' : ''}">
					<td class="text-center"><input type="checkbox" ${checked} ${disabled} data-name="${r.name}"></td>
					<td>${r.course_name || ""}</td>
					<td>${r.course_code || ""}</td>
					<td>${r.department_name || r.department || ""}</td>
					<td>${r.credit_value || 0}</td>
					<td>${statusHtml}</td>
				</tr>
			`);

			if (!isAlreadyAdded) {
				tr.find("input").on("change", function () {
					if (this.checked) selected.add(r);
					else selected.delete(r);

					// Update master checkbox state
					const allNowSelected = selectableRows.every(row => selected.has(row.name));
					selectAll.prop("checked", allNowSelected);
				});

				// Allow clicking row to toggle (user experience improvement)
				tr.on("click", function (e) {
					if (e.target.type !== 'checkbox') {
						const $cb = $(this).find("input[type='checkbox']");
						$cb.prop("checked", !$cb.prop("checked")).trigger("change");
					}
				});
			}

			tbody.append(tr);
		});

		wrapper.append(table);
	}

	// Initial load
	load_courses();
}



function edit_course_dialog(frm, item, course_fields) {
	// Dynamically build fields
	let dialogFields = [];

	// Always include credits (mapped to credit_value in Course, but credits in CurriculumItem)
	dialogFields.push({
		label: "Credits",
		fieldname: "credits", // internal name in curriculum item
		fieldtype: "Int",
		default: item.credits || item.credit_value,
		reqd: 1,
	});

	/*
	   If we want to allow editing other fields, we need to know if they are strictly 'override' fields
	   or just read-only from Course.
	   Typically curriculum overrides credits. Other fields like Name/Department are fixed from Course.
	   The user request says "Edit credit value syncs correctly".
	   It doesn't explicitly ask to edit OTHER fields.
	   But it asks for "Changes in Course DocType... reflected".
	   This implies READ-ONLY view of other fields.
	   So we don't need to add them to the Edit Dialog.
	   We only need to ensure they SHOW UP in the UI Container.
	*/

	const d = new frappe.ui.Dialog({
		title: "Edit Course",
		fields: dialogFields,
		primary_action_label: "Update",
		primary_action: function (values) {
			// Update the item reference
			item.credits = values.credits;

			// If we had other overrides, update them here.

			frm.active_term_name = item.semester;
			frm.trigger("render_ui");
			frm.trigger("save_curriculum");
			d.hide();
		},
	});
	d.show();
}

function edit_cluster_dialog(frm, item) {
	const d = new frappe.ui.Dialog({
		title: "Edit Cluster",
		fields: [
			{
				label: "Cluster Name",
				fieldname: "cluster_name",
				fieldtype: "Data",
				default: item.cluster_name,
				reqd: 1,
			},
			{
				label: "Min Courses",
				fieldname: "min_courses",
				fieldtype: "Int",
				default: item.min_courses,
				reqd: 1,
			},
			{
				label: "Max Courses",
				fieldname: "max_courses",
				fieldtype: "Int",
				default: item.max_courses,
				reqd: 1,
			},
		],
		primary_action_label: "Update",
		primary_action: function (values) {
			Object.assign(item, values);
			frm.active_term_name = item.semester;
			frm.trigger("render_ui");
			frm.trigger("save_curriculum");
			d.hide();
		},
	});
	d.show();
}

function add_cluster_dialog(frm, semester, enrollment_type) {
	const d = new frappe.ui.Dialog({
		title: "Add Cluster",
		fields: [
			{ label: "Cluster Name", fieldname: "cluster_name", fieldtype: "Data", reqd: 1 },
			{
				label: "Min Courses",
				fieldname: "min_courses",
				fieldtype: "Int",
				reqd: 1,
				default: 1,
			},
			{
				label: "Max Courses",
				fieldname: "max_courses",
				fieldtype: "Int",
				reqd: 1,
				default: 1,
			},
		],
		primary_action_label: "Add",
		primary_action: function (values) {
			if (!frm.curriculum_data.curriculum_courses)
				frm.curriculum_data.curriculum_courses = [];

			frm.curriculum_data.curriculum_courses.push({
				semester: semester,
				enrollment_type: enrollment_type,
				course_group_type: "Cluster",
				...values,
			});

			frm.active_term_name = semester;
			frm.trigger("render_ui");
			frm.trigger("save_curriculum");
			d.hide();
		},
	});
	d.show();
}
