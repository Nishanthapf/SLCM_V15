// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.ui.form.on("Course Management", {
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

		// Persistence: Restore filters
		if (!frm.doc.department && !frm.doc.program && !frm.doc.academic_year) {
			const settings = frappe.model.user_settings[frm.doctype] || {};
			if (settings.filters) {
				if (settings.filters.department) frm.set_value("department", settings.filters.department);
				if (settings.filters.program) frm.set_value("program", settings.filters.program);
				if (settings.filters.academic_year) frm.set_value("academic_year", settings.filters.academic_year);
				if (settings.filters.batch) frm.set_value("batch", settings.filters.batch);
				if (settings.filters.section) frm.set_value("section", settings.filters.section);
			}
		}

		// Load UI if data already present
		if (frm.doc.department && frm.doc.program && frm.doc.academic_year) {
			frm.trigger("autorefresh");
		} else if (frm.curriculum_data) {
			// If we have curriculum data but filters changed, re-render to pick up settings changes
			frm.trigger("render_ui");
		}

		frm.add_custom_button(__("Reset Filters"), function () {
			frm.set_value("department", "");
			frm.set_value("program", "");
			frm.set_value("academic_year", "");
			frm.set_value("batch", "");
			frm.set_value("section", "");
			frm.curriculum_data = null;
			// Clear persistence
			frappe.model.user_settings.save(frm.doctype, "filters", null);
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
		// Persistence: Save filters
		frappe.model.user_settings.save(frm.doctype, "filters", {
			department: frm.doc.department,
			program: frm.doc.program,
			academic_year: frm.doc.academic_year,
			batch: frm.doc.batch,
			section: frm.doc.section
		});
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
				method: "slcm.slcm.doctype.course_management.course_management.get_details_from_section",
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
				method: "slcm.slcm.doctype.course_management.course_management.get_curriculum",
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

		// USE COURSE TYPES FOR GROUPING
		const course_types = (frm.doc.course_types || []).filter((d) => d.is_active);
		// Also get enrollment types for the dropdowns later (if needed) or button logic
		// But grouping is strictly course_types now.

		const system = frm.doc.academic_system || "Semester";

		let defaultCount = 8;
		if (system === "Trimester") defaultCount = 3;
		else if (system === "Quarter") defaultCount = 4;
		else if (system === "Year") defaultCount = 5;

		let activeTerms = new Set(frm.term_list || []);
		for (let i = 1; i <= defaultCount; i++) activeTerms.add(i);

		(frm.curriculum_data.curriculum_courses || []).forEach((c) => {

			// -----------------------------------------------------------------------------
			// MIGRATION LOGIC (On the fly view adaptation)
			// -----------------------------------------------------------------------------
			// If old data (enrollment_type is 'Core' but course_type is missing)
			// We should treat it as course_type='Core'.
			if (!c.course_type && c.enrollment_type) {
				// Check if this enrollment_type is one of our Active Course Types
				// Or check if it is NOT one of our Enrollment Types (Full/Audit) - better heuristic?
				// Actually, if it's missing course_type, we can just default it to enrollment_type
				// IF that value matches one of the current Group Headers we are about to render (course_types)

				const validCTs = course_types.map(x => x.course_type);
				// Also include any "Legacy" types that might be in the system but not active?
				// User said "all active type should be there".

				if (validCTs.includes(c.enrollment_type)) {
					c.course_type = c.enrollment_type;
				}
				// If NOT in validCTs, it won't render in the grouped sections below anyway, 
				// unless we dynamically Add to course_types list?
				// But we iterate 'course_types' to create sections.
			}

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

		// Get active enrollment types from settings
		const enrollment_types = (frm.doc.enrollment_types || []).filter((d) => d.is_active);

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

			// GROUP 1: Course Types
			if (course_types.length > 0) {
				$etContainer.append(`<h6 class="text-uppercase text-muted font-weight-bold mb-3 mt-2" style="font-size: 11px; letter-spacing: 1px;">Course Types</h6>`);

				course_types.forEach((ct) => {
					const sectionCourses = coursesInSem.filter(
						(c) => c.course_type === ct.course_type
					);

					const courseCount = sectionCourses.length;
					const countBadge = courseCount > 0
						? `<span class="badge badge-secondary ml-2" style="font-size: 10px;">${courseCount} Selected</span>`
						: `<span class="badge badge-light ml-2 text-muted" style="font-size: 10px;">0 Selected</span>`;

					const customButtons = `
						<button class="btn btn-xs btn-default btn-add-course"
							data-sem="${termName}" data-ct="${ct.course_type}">+ Add Course</button>
						${ct.course_type !== "Core"
							? `<button class="btn btn-xs btn-default btn-add-cluster ml-1"
								data-sem="${termName}" data-ct="${ct.course_type}">+ Add Cluster</button>`
							: ""
						}
					`;

					const courseTypeHtml = `
	                    <div class="course-type-section mb-4" style="border-left: 3px solid #333; padding-left: 15px;">
	                        <div class="d-flex justify-content-between align-items-center mb-2">
	                            <h6 class="font-weight-bold text-dark mb-0" style="font-size: 13px;">
	                                ${ct.display_name || ct.course_type}
	                                ${countBadge}
	                            </h6>
	                            <div>
	                                ${customButtons}
	                            </div>
	                        </div>
	                        <div class="list-group">
	                            ${sectionCourses
							.map((course, idx) =>
								render_course_item(
									course,
									idx,
									termName,
									ct.course_type,
									course_fields,
									null
								)
							)
							.join("")}
	                        </div>
	                    </div>
	                `;
					$etContainer.append(courseTypeHtml);
				});
			}

			// GROUP 2: Enrollment Types
			if (enrollment_types.length > 0) {
				$etContainer.append(`<h6 class="text-uppercase text-muted font-weight-bold mb-3 mt-4" style="font-size: 11px; letter-spacing: 1px;">Enrollment Types</h6>`);

				enrollment_types.forEach((et) => {
					// Only show if no Course Type defined (avoids duplication with Group 1)
					const sectionCourses = coursesInSem.filter(
						(c) => c.enrollment_type === et.enrollment_type && !c.course_type
					);

					const totalCount = sectionCourses.length;
					const enrollmentCountBadge = totalCount > 0
						? `<span class="badge badge-secondary ml-2" style="font-size: 10px;">${totalCount} Selected</span>`
						: `<span class="badge badge-light ml-2 text-muted" style="font-size: 10px;">0 Selected</span>`;

					const customButtons = `
						<button class="btn btn-xs btn-default btn-add-course"
							data-sem="${termName}" data-et="${et.enrollment_type}">+ Add Course</button>
						<button class="btn btn-xs btn-default btn-add-cluster ml-1"
							data-sem="${termName}" data-et="${et.enrollment_type}">+ Add Cluster</button>
					`;

					const enrollmentTypeHtml = `
	                    <div class="enrollment-type-section mb-4" style="border-left: 3px solid #007bff; padding-left: 15px;">
	                        <div class="d-flex justify-content-between align-items-center mb-3">
	                            <h6 class="font-weight-bold mb-0 text-dark" style="font-size: 13px;">
	                                ${et.display_name || et.enrollment_type}
	                                ${enrollmentCountBadge}
	                            </h6>
	                             <div>
	                                ${customButtons}
	                            </div>
	                        </div>
	                        <div class="list-group">
	                             ${sectionCourses
							.map((course, idx) =>
								render_course_item(
									course,
									idx,
									termName,
									null,
									course_fields,
									et.enrollment_type
								)
							)
							.join("")}
	                        </div>
	                    </div>
	                `;
					$etContainer.append(enrollmentTypeHtml);
				});
			}
		});

		if (frm.active_term_name) delete frm.active_term_name;

		// Bind Events
		$container.find(".btn-add-course").on("click", function (e) {
			e.preventDefault();
			const enrollmentType = $(this).data("et");
			add_course_dialog(frm, $(this).data("sem"), $(this).data("ct"), course_fields, enrollmentType);
		});

		$container.find(".btn-add-cluster").on("click", function (e) {
			e.preventDefault();
			const enrollmentType = $(this).data("et");
			add_cluster_dialog(frm, $(this).data("sem"), $(this).data("ct"), enrollmentType);
		});

		$container.find(".btn-add-term").on("click", function (e) {
			e.preventDefault();
			const max = frm.term_list.length > 0 ? Math.max(...frm.term_list) : 0;
			frm.term_list.push(max + 1);
			frm.trigger("render_ui");
		});

		$container.find(".btn-remove-terms").on("click", function (e) {
			e.preventDefault();
			remove_term_dialog(frm, system, defaultCount);
		});

		// Delegation for Edit/Remove
		$container.on("click", ".edit-course", function (e) {
			// Implementation for edit skipped as requested only Add logic changes primarily
			// But remove logic is below
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
			method: "slcm.slcm.doctype.course_management.course_management.save_curriculum",
			args: {
				program: frm.doc.program,
				academic_year: frm.doc.academic_year,
				department: frm.doc.department,
				academic_system: frm.doc.academic_system,
				batch: frm.doc.batch,
				section: frm.doc.section,
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

// -----------------------------------------------------------------------------
// HELPER FUNCTIONS
// -----------------------------------------------------------------------------

function find_item_by_data(frm, $el) {
	const sem = $el.data("sem");
	const ct = $el.data("ct"); // Changed from et
	const courseName = $el.data("course");
	const clusterName = $el.data("cluster");
	const isCluster = !!clusterName;

	return (frm.curriculum_data.curriculum_courses || []).find((c) => {
		// Match against course_type
		// Logic handles migrated data (fallback to enrollment_type if course_type missing)
		// We use a loose fallback to support ANY legacy type
		const cType = c.course_type || c.enrollment_type;

		if (c.semester === sem && cType === ct) {
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
	const courseName = $el.data("course");
	const clusterName = $el.data("cluster");
	const isCluster = !!clusterName;
	const sem = $el.data("sem");
	const ct = $el.data("ct");
	const et = $el.data("et");

	let confirmMsg = "";
	if (isCluster) {
		confirmMsg = __("Are you sure you want to remove cluster <b>{0}</b>?", [clusterName]);
	} else {
		confirmMsg = __("Are you sure you want to remove course <b>{0}</b>?", [courseName]);
	}

	frappe.confirm(confirmMsg, () => {
		let list = frm.curriculum_data.curriculum_courses || [];
		let deleted = false;

		// Update finding logic to be specific
		frm.curriculum_data.curriculum_courses = list.filter((c) => {
			// If already deleted one instance (for this specific button click), keep others
			if (deleted) return true;

			// Match Semester
			if (c.semester !== sem) return true;

			// Match Context
			// If button has CT, course must match CT
			if (ct && c.course_type !== ct) return true;
			// If button has ET, course must match ET
			if (et && c.enrollment_type !== et) return true;

			// Match Item
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
			return true;
		});

		if (deleted) {
			frm.active_term_name = sem;
			frm.trigger("render_ui");
			frm.trigger("save_curriculum");
		}
	});
}

function render_course_item(course, idx, resultSem, resultCt, course_fields, resultEt) {
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
                            data-sem="${resultSem}" data-ct="${resultCt}" data-et="${resultEt || ''}" data-cluster="${course.cluster_name}">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
	} else {
		// DYNAMIC FIELD RENDERING
		let infoParts = [];
		// Always show credits
		infoParts.push(`Credits: ${course.credits || course.credit_value || 0}`);

		// COURSE TYPE DISPLAY
		// Show internal Course Type only if it's NOT the current Section Header context
		if (course.course_type && course.course_type !== resultCt) {
			infoParts.push(`<strong>Type:</strong> ${course.course_type}`);
		}

		// ENROLLMENT TYPE DISPLAY
		// Show Enrollment Type only if:
		// 1. It is NOT the current Section Header context
		// 2. It is NOT "Full" (Implicit default, redudant info)
		// 3. It is a special type (Audit, Zero Credit, etc.)
		if (course.enrollment_type &&
			course.enrollment_type !== resultEt &&
			course.enrollment_type !== "Full" &&
			!["Core", "Programme Elective", "Open Elective", "Seminar"].includes(course.enrollment_type)) {

			let badgeClass = "badge-secondary";
			if (course.enrollment_type === "Audit") badgeClass = "badge-warning";
			else if (course.enrollment_type === "Zero Credit") badgeClass = "badge-info";

			infoParts.push(`<strong>Enrollment:</strong> <span class="badge ${badgeClass}">${course.enrollment_type}</span>`);
		}

		// Add other fields if they have value (optional)
		course_fields.forEach((f) => {
			if (
				f.fieldname !== "course_name" &&
				f.fieldname !== "credit_value" &&
				f.fieldname !== "course_type" &&
				f.fieldname !== "enrollment_type" &&
				course[f.fieldname]
			) {
				// skip internal fields
				infoParts.push(`${f.label}: ${course[f.fieldname]}`);
			}
		});

		return `
            <div class="list-group-item p-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${course.course}</strong><br>
                        <small class="text-muted">${infoParts.join(" | ")}</small>
                    </div>
                    <div>
                         <button class="btn btn-xs text-danger remove-course"
                            data-sem="${resultSem}" data-ct="${resultCt}" data-et="${resultEt || ''}" data-course="${course.course}">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
	}
}

// remove_term_dialog skipped in this chunk because it doesn't need specific changes (it filters by semester)

function add_course_dialog(frm, semester, course_type, course_fields, enrollment_type) {
	let selected = new Map(); // Use Map for ID-based tracking
	// Logic: "Not Both". If context is CT, hide ET. If context is ET, hide CT.

	// Get available Enrollment Types
	const enrollment_types_opts = (frm.doc.enrollment_types || [])
		.filter(d => d.is_active && !["Core", "Programme Elective", "Open Elective", "Seminar"].includes(d.enrollment_type))
		.map(d => d.enrollment_type);

	if (enrollment_types_opts.length === 0) enrollment_types_opts.push("Full", "Audit", "Zero Credit");

	// Get available Course Types
	const course_types_opts = (frm.doc.course_types || [])
		.filter(d => d.is_active)
		.map(d => d.course_type);

	// Context Title
	let titleSuffix = "";
	if (course_type) titleSuffix = `Course Type: ${course_type}`;
	else if (enrollment_type) titleSuffix = `Enrollment: ${enrollment_type}`;

	const d = new frappe.ui.Dialog({
		title: `Add Courses - ${titleSuffix}`,
		size: "extra-large",
		fields: [
			{
				fieldtype: "Data",
				fieldname: "search",
				label: "Search",
				onchange() { load_courses(); },
			},
			{
				fieldtype: "Link",
				fieldname: "department",
				label: "Department",
				options: "Department",
				default: frm.doc.department,
				onchange() { load_courses(); },
			},
			{
				fieldtype: "Select",
				fieldname: "enrollment_type",
				label: "Enrollment Type",
				options: enrollment_types_opts,
				default: enrollment_type || "Full",
				read_only: !!enrollment_type,
				reqd: 1,
				hidden: !!course_type // Hide if adding to Course Type (Implicitly Full)
			},
			{
				fieldtype: "Select",
				fieldname: "course_type",
				label: "Course Type",
				options: course_types_opts,
				default: course_type || null,
				read_only: !!course_type,
				reqd: 0, // Not required if adding to Enrollment Type
				hidden: !!enrollment_type // Hide if adding to Enrollment Type
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
			let selectedEt = d.get_value("enrollment_type");
			let selectedCt = d.get_value("course_type");

			// If hidden/empty, ensure clean values
			if (d.fields_dict.course_type.df.hidden) selectedCt = null;
			// If et hidden, it defaults to 'Full' via field default logic, or we enforce it here
			if (d.fields_dict.enrollment_type.df.hidden && !selectedEt) selectedEt = "Full";

			selected.forEach((c) => {
				// Check duplicate using BOTH types for uniqueness?
				// Actually, duplicate implies "Same Course" appearing in "Same Context".
				// But here we allow duplicates if checking from different view.
				// However, data structure is list.
				// If I add SAME course with SAME CT and SAME ET, it is duplicate.
				const exists = frm.curriculum_data.curriculum_courses.find(
					(e) =>
						e.semester === semester &&
						e.course_type === selectedCt &&
						e.enrollment_type === selectedEt &&
						e.course_group_type === "Course" &&
						e.course === c.name
				);

				if (exists) return;

				frm.curriculum_data.curriculum_courses.push({
					semester: semester,
					course_type: selectedCt,
					enrollment_type: selectedEt,
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
		const table = $(`<table class="table table-bordered table-hover"><thead><tr><th style="width:40px; text-align: center;"><input type="checkbox" class="select-all"></th><th>Course Name</th><th>Course Code</th><th>Department</th><th>Credits</th><th>Status</th></tr></thead><tbody></tbody></table>`);
		const tbody = table.find("tbody");
		const selectAll = table.find(".select-all");

		// Logic to check existing
		const existingCourses = new Set();
		if (frm.curriculum_data.curriculum_courses) {
			frm.curriculum_data.curriculum_courses.forEach(c => {
				if (c.semester === semester && c.course_group_type === "Course") existingCourses.add(c.course);
			});
		}

		const selectableRows = rows.filter(r => !existingCourses.has(r.name));

		// Update master check state based on Map
		const allSelected = selectableRows.length > 0 && selectableRows.every(r => selected.has(r.name));
		selectAll.prop("checked", allSelected);
		if (selectableRows.length === 0) selectAll.prop("disabled", true);

		// Handle Select All Click
		selectAll.on("change", function () {
			const isChecked = $(this).prop("checked");
			selectableRows.forEach(r => {
				const $cb = tbody.find(`.course-checkbox[data-name='${r.name}']`);
				$cb.prop("checked", isChecked); // Update UI
				if (isChecked) selected.set(r.name, r);
				else selected.delete(r.name);
			});
		});

		if (rows.length === 0) {
			tbody.append(`<tr><td colspan="6" class="text-center text-muted">No courses found</td></tr>`);
		} else {
			rows.forEach(r => {
				const isExisting = existingCourses.has(r.name);
				const isSelected = selected.has(r.name); // Correct check for Map
				const tr = $(`<tr class="${isExisting ? 'table-active text-muted' : ''}"><td class="text-center"><input type="checkbox" class="course-checkbox" data-name="${r.name}" ${isExisting ? 'disabled checked' : ''} ${isSelected ? 'checked' : ''}></td><td>${r.course_name} <br><small class="text-muted">${r.name}</small></td><td>${r.course_code}</td><td>${r.department}</td><td>${r.credit_value} Credit(s)</td><td>${r.status}</td></tr>`).appendTo(tbody);

				if (!isExisting) {
					// Handle Individual Click
					tr.find(".course-checkbox").on("change", function () {
						if ($(this).is(":checked")) selected.set(r.name, r);
						else selected.delete(r.name);

						// Update master checkbox state
						const currentAll = selectableRows.every(row => selected.has(row.name));
						selectAll.prop("checked", currentAll);
					});

					// Row click convenience
					tr.on("click", function (e) {
						if (e.target.type !== 'checkbox') {
							const $cb = $(this).find("input[type='checkbox']");
							$cb.prop("checked", !$cb.prop("checked")).trigger("change");
						}
					});
				}
			});
		}
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

function add_cluster_dialog(frm, semester, course_type, enrollment_type) {
	// Get available Course Types
	const course_types_opts = (frm.doc.course_types || [])
		.filter(d => d.is_active)
		.map(d => d.course_type);

	// Get available Enrollment Types
	const enrollment_types_opts = (frm.doc.enrollment_types || [])
		.filter(d => d.is_active && !["Core", "Programme Elective", "Open Elective", "Seminar"].includes(d.enrollment_type))
		.map(d => d.enrollment_type);

	if (enrollment_types_opts.length === 0) enrollment_types_opts.push("Full", "Audit", "Zero Credit");

	const titleSuffix = course_type ? `Course Type: ${course_type}` : `Enrollment: ${enrollment_type}`;

	const d = new frappe.ui.Dialog({
		title: `Add Cluster - ${titleSuffix}`,
		fields: [
			{ label: "Cluster Name", fieldname: "cluster_name", fieldtype: "Data", reqd: 1 },
			{
				label: "Course Type",
				fieldname: "course_type",
				fieldtype: "Select",
				options: course_types_opts,
				default: course_type || null,
				read_only: !!course_type,
				hidden: !!course_type,
				reqd: 1
			},
			{
				label: "Enrollment Type",
				fieldname: "enrollment_type",
				fieldtype: "Select",
				options: enrollment_types_opts,
				default: enrollment_type || "Full",
				read_only: !!enrollment_type,
				reqd: 1
			},
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

			const selectedCt = values.course_type || course_type;
			const selectedEt = values.enrollment_type || enrollment_type || "Full";

			frm.curriculum_data.curriculum_courses.push({
				semester: semester,
				course_type: selectedCt,
				enrollment_type: selectedEt,
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
