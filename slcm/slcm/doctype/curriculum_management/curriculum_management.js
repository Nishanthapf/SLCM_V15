// Copyright (c) 2026, Administrator and contributors
// For license information, please see license.txt

frappe.ui.form.on("Curriculum Management", {
    refresh: function (frm) {
        frm.disable_save();

        // Load UI if data already present (e.g. after refresh)
        if (frm.doc.department && frm.doc.program && frm.doc.academic_year) {
            frm.trigger("autorefresh");
        }


        frm.add_custom_button(__("Reset Filters"), function () {
            frm.set_value("department", "");
            frm.set_value("program", "");
            frm.set_value("academic_year", "");
            frm.curriculum_data = null;
            frm.trigger("render_ui");
        });

        // Add a custom Save button for the Curriculum tab via page action
        frm.page.set_primary_action("Save", function () {
            // Trigger standard form save
            frm.save().then(() => {
                // Then save curriculum data if valid
                if (frm.doc.program && frm.doc.academic_year) {
                    frm.trigger("save_curriculum");
                }
            });
        });
    },

    onload: function (frm) {
        // Ensure defaults are loaded if new
        if (frm.is_new()) {
            frm.trigger("set_defaults");
        }
    },

    set_defaults: function (frm) {
        // This is handled by python onload, but we can trigger it
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
        frm.trigger("render_ui");
    },

    autorefresh: function (frm) {
        frm.trigger("load_curriculum");
    },

    load_curriculum: function (frm) {
        if (frm.doc.department && frm.doc.program && frm.doc.academic_year) {
            frappe.call({
                method: "slcm.slcm.doctype.curriculum_management.curriculum_management.get_curriculum",
                args: {
                    program: frm.doc.program,
                    academic_year: frm.doc.academic_year,
                },
                callback: function (r) {
                    if (r.message) {
                        frm.curriculum_data = r.message;

                        // Sync system from DB if exists (Backend value overrides current form default only if they differ significantly or if we want to enforce backend truth)
                        // However, if we just fetched from Academic Year, we should ideally respect that unless the specific curriculum overrides it.
                        // Let's say specific curriculum persistence > Academic Year default.

                        if (r.message.academic_system) {
                            // If backend has a stored system, use it.
                            if (frm.doc.academic_system !== r.message.academic_system) {
                                frm.set_value("academic_system", r.message.academic_system).then(
                                    () => {
                                        frm.trigger("render_ui");
                                    }
                                );
                                return; // Wait for set_value promise
                            }
                        }

                        frm.trigger("render_ui");
                    }
                },
            });
        } else {
            $(frm.fields_dict.ui_container.wrapper).html(
                '<div class="text-muted text-center p-5">Please select Department, Program and Year</div>'
            );
        }
    },

    render_ui: function (frm) {
        const wrapper = $(frm.fields_dict.ui_container.wrapper);

        // Capture currently open tab to restore state
        const activeTermId = wrapper.find(".collapse.show").attr("id");

        wrapper.empty();

        if (!frm.curriculum_data) return;

        // Helper to get active enrollment types
        const enrollment_types = (frm.doc.enrollment_types || []).filter((d) => d.is_active);

        // Determine terms based on system
        const system = frm.doc.academic_system || "Semester";
        let defaultCount = 8;
        if (system === "Trimester") defaultCount = 3;
        else if (system === "Quarter") defaultCount = 4;
        else if (system === "Year") defaultCount = 5;

        // Calculate max term from existing data
        // Use a Set to track all active terms
        if (!frm.term_list) {
            let activeTerms = new Set();
            // Add Defaults
            for (let i = 1; i <= defaultCount; i++) activeTerms.add(i);

            // Add from Data
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
        }

        // Basic Template
        const html = `
			<div class="curriculum-manager">
				<div class="clearfix mb-3">
					<!-- Helper text or sub-header -->
					<div class="text-muted small float-left">
						Configure courses for ${frm.curriculum_data.program} (${frm.curriculum_data.academic_year}) - <b>${system} System</b>
					</div>
				</div>

				<div class="card mb-3">
					<div class="card-header">
						<h5 class="mb-0">Term Dependent Curriculum</h5>
					</div>
					<div class="card-body p-0">
						<div class="accordion" id="accordionSemesters">
							<!-- Semesters will go here -->
						</div>
					</div>
						</div>
					</div>
					<div class="card-footer p-2 text-center">
						<button class="btn btn-sm btn-default btn-add-term">
							+ Add ${system}
						</button>
						<button class="btn btn-sm btn-danger btn-remove-terms ml-2">
							- Remove ${system}
						</button>
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
							<h6 class="font-weight-bold" style="text-transform: uppercase; font-size: 11px; letter-spacing: 1px; color: #777;">
								${et.display_name || et.enrollment_type}
							</h6>
							<div>
								<button class="btn btn-xs btn-default btn-add-course" data-sem="${termName}" data-et="${et.enrollment_type
                    }">+ Add Course</button>
								${et.enrollment_type !== "Core"
                        ? `<button class="btn btn-xs btn-default btn-add-cluster ml-1" data-sem="${termName}" data-et="${et.enrollment_type}">+ Add Cluster</button>`
                        : ""
                    }
							</div>
						</div>
						<div class="course-list list-group" id="list-${term}-${et.enrollment_type.replace(
                        /[^a-zA-Z0-9]/g,
                        ""
                    )}">
							${etCourses
                        .map((course, idx) =>
                            render_course_item(course, idx, termName, et.enrollment_type)
                        )
                        .join("")}
						</div>
					</div>
				`;
                $etContainer.append(etHtml);
            });
        });

        // Cleanup active term hint after render (only if strictly needed, but keeps state clean)
        if (frm.active_term_name) delete frm.active_term_name;

        // Bind Events
        $container.find(".btn-save-curriculum").on("click", function () {
            frm.trigger("save_curriculum");
        });

        $container.find(".btn-add-course").on("click", function (e) {
            e.preventDefault();
            const sem = $(this).data("sem");
            const et = $(this).data("et");
            add_course_dialog(frm, sem, et);
        });

        $container.find(".btn-add-cluster").on("click", function (e) {
            e.preventDefault();
            const sem = $(this).data("sem");
            const et = $(this).data("et");
            add_cluster_dialog(frm, sem, et);
        });

        $container.find(".btn-add-term").on("click", function (e) {
            e.preventDefault();
            // Logic: Add max + 1
            const max = frm.term_list.length > 0 ? Math.max(...frm.term_list) : 0;
            frm.term_list.push(max + 1);
            frm.trigger("render_ui");
        });


        $container.find(".btn-remove-terms").on("click", function (e) {
            e.preventDefault();

            // Dialog to select terms
            const d = new frappe.ui.Dialog({
                title: `Remove ${system}s`,
                fields: [
                    {
                        fieldtype: "MultiCheck",
                        label: "Select Terms to Remove",
                        fieldname: "terms",
                        options: frm.term_list.map(t => ({
                            label: `${system} ${t}`,
                            value: t
                        })),
                        columns: 2
                    }
                ],
                primary_action_label: "Remove Selected",
                primary_action: (values) => {
                    const toRemove = values.terms || [];
                    if (toRemove.length === 0) return;

                    // Check for restricted defaults
                    const restricted = toRemove.filter(t => t <= defaultCount);
                    if (restricted.length > 0) {
                        frappe.msgprint({
                            title: __("Cannot Remove Defaults"),
                            message: __(`The following ${system.toLowerCase()}s are part of the default structure and cannot be removed: <b>${restricted.join(", ")}</b>`),
                            indicator: 'orange'
                        });
                        return;
                    }

                    // 1. Remove Data
                    const removeNames = toRemove.map(t => `${system} ${t}`);
                    if (frm.curriculum_data.curriculum_courses) {
                        frm.curriculum_data.curriculum_courses = frm.curriculum_data.curriculum_courses.filter(
                            (c) => !removeNames.includes(c.semester)
                        );
                    }

                    // 2. Remove from list
                    frm.term_list = frm.term_list.filter(t => !toRemove.includes(t));

                    // 3. Render and Save
                    frm.trigger("render_ui");
                    frm.trigger("save_curriculum");
                    d.hide();
                }
            });
            d.show();
        });

        $container.on("click", ".edit-course", function (e) {
            e.preventDefault();
            const sem = $(this).data("sem");
            const et = $(this).data("et");
            const courseName = $(this).data("course");
            const clusterName = $(this).data("cluster");
            const isCluster = !!clusterName;

            const item = frm.curriculum_data.curriculum_courses.find((c) => {
                if (c.semester === sem && c.enrollment_type === et) {
                    if (
                        isCluster &&
                        c.course_group_type === "Cluster" &&
                        c.cluster_name === clusterName
                    )
                        return true;
                    if (
                        !isCluster &&
                        c.course_group_type === "Course" &&
                        c.course === courseName
                    )
                        return true;
                }
                return false;
            });

            if (item) {
                if (isCluster) edit_cluster_dialog(frm, item);
                else edit_course_dialog(frm, item);
            }
        });

        $container.on("click", ".remove-course", function (e) {
            e.preventDefault();
            const sem = $(this).data("sem");
            const et = $(this).data("et");

            // Find index in main array
            // We need to match precise object. simpler if we use a unique ID, but for now filtering.
            // Let's filter out the specific item.
            // Since we re-render, we can't trust index if data changed.
            // But we passed simple iteration index.
            // Let's rely on filter logic: remove one instance of this config.

            const courseName = $(this).data("course");
            const clusterName = $(this).data("cluster");
            const isCluster = !!clusterName;

            let deleted = false;
            frm.curriculum_data.curriculum_courses = frm.curriculum_data.curriculum_courses.filter(
                (c) => {
                    if (deleted) return true; // already deleted one
                    if (c.semester === sem && c.enrollment_type === et) {
                        if (
                            isCluster &&
                            c.course_group_type === "Cluster" &&
                            c.cluster_name === clusterName
                        ) {
                            deleted = true;
                            return false;
                        }
                        if (
                            !isCluster &&
                            c.course_group_type === "Course" &&
                            c.course === courseName
                        ) {
                            deleted = true;
                            return false;
                        }
                    }
                    return true;
                }
            );

            frm.active_term_name = sem;
            frm.trigger("render_ui");
            frm.trigger("save_curriculum");
        });
    },

    save_curriculum: function (frm) {
        if (!frm.curriculum_data) return;

        // Add department from filter if missing
        if (!frm.doc.department) {
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

function render_course_item(course, idx, resultSem, resultEt) {
    if (course.course_group_type === "Cluster") {
        return `
			<div class="list-group-item p-2">
				<div class="d-flex justify-content-between align-items-center">
					<div>
						<strong>${course.cluster_name}</strong> <span class="badge badge-info ml-1">Cluster</span><br>
						<small class="text-muted">Min: ${course.min_courses}, Max: ${course.max_courses}</small>
					</div>
					<div>
						<button class="btn btn-xs text-muted edit-course mr-1" data-sem="${resultSem}" data-et="${resultEt}" data-cluster="${course.cluster_name}">
							<i class="fa fa-pencil"></i>
						</button>
						<button class="btn btn-xs text-danger remove-course" data-sem="${resultSem}" data-et="${resultEt}" data-cluster="${course.cluster_name}">
							<i class="fa fa-times"></i>
						</button>
					</div>
				</div>
			</div>
		`;
    } else {
        return `
			<div class="list-group-item p-2">
				<div class="d-flex justify-content-between align-items-center">
					<div>
						<strong>${course.course}</strong><br>
						<small class="text-muted">Credits: ${course.credits || "-"}</small>
					</div>
					<div>
						<button class="btn btn-xs text-muted edit-course mr-1" data-sem="${resultSem}" data-et="${resultEt}" data-course="${course.course}">
							<i class="fa fa-pencil"></i>
						</button>
						<button class="btn btn-xs text-danger remove-course" data-sem="${resultSem}" data-et="${resultEt}" data-course="${course.course}">
							<i class="fa fa-times"></i>
						</button>
					</div>
				</div>
			</div>
		`;
    }
}

function add_course_dialog(frm, semester, enrollment_type) {
    new frappe.ui.form.MultiSelectDialog({
        doctype: "Course",
        target: frm,
        setters: {
            department: frm.doc.department,
        },
        add_filters_group: 1,
        get_query() {
            return {
                filters: {
                    department: frm.doc.department,
                },
            };
        },
        action(selections) {
            if (selections.length === 0) return;

            frappe.db
                .get_list("Course", {
                    filters: { name: ["in", selections] },
                    fields: ["name", "credit_value"],
                })
                .then((courses) => {
                    if (!frm.curriculum_data.curriculum_courses)
                        frm.curriculum_data.curriculum_courses = [];

                    courses.forEach((c) => {
                        // Avoid duplicates if needed, or allow
                        frm.curriculum_data.curriculum_courses.push({
                            semester: semester,
                            enrollment_type: enrollment_type,
                            course_group_type: "Course",
                            course: c.name,
                            credits: c.credit_value,
                        });
                    });

                    frm.active_term_name = semester;
                    frm.trigger("render_ui");
                    frm.trigger("save_curriculum");
                    cur_dialog.hide();
                });
        },
    });
}

function edit_course_dialog(frm, item) {
    const d = new frappe.ui.Dialog({
        title: "Edit Course",
        fields: [
            {
                label: "Credits",
                fieldname: "credits",
                fieldtype: "Float",
                default: item.credits,
                reqd: 1,
            },
        ],
        primary_action_label: "Save",
        primary_action: function (values) {
            item.credits = values.credits;
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
        primary_action_label: "Save",
        primary_action: function (values) {
            item.cluster_name = values.cluster_name;
            item.min_courses = values.min_courses;
            item.max_courses = values.max_courses;
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
        primary_action_label: "Add",
        primary_action: function (values) {
            if (!frm.curriculum_data.curriculum_courses)
                frm.curriculum_data.curriculum_courses = [];

            frm.curriculum_data.curriculum_courses.push({
                semester: semester,
                enrollment_type: enrollment_type,
                course_group_type: "Cluster",
                cluster_name: values.cluster_name,
                min_courses: values.min_courses,
                max_courses: values.max_courses,
            });

            frm.active_term_name = semester;
            frm.trigger("render_ui");
            frm.trigger("save_curriculum");
            d.hide();
        },
    });
    d.show();
}
