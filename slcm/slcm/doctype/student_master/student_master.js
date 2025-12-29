// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Student Master", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Student Master", {
	refresh(frm) {
		// Hide default left sidebar
		$(".layout-side-section").hide();

		// Render custom right-side profile panel
		frm.trigger("render_profile_sidebar");
	},

	render_profile_sidebar(frm) {
		if (frm.is_new()) {
			return;
		}

		const image = frm.doc.student_image || "/assets/frappe/images/default-avatar.png";

		const html = `
			<div class="student-profile-card">
				<img src="${image}" class="student-avatar" />
				<button class="btn btn-sm btn-primary upload-btn">
					Upload Image
				</button>
				<hr />
				<div class="attachment-area">
					<h6>Attachments</h6>
					<div class="attachments"></div>
				</div>
			</div>
		`;

		frm.fields_dict.profile_sidebar.$wrapper.html(html);

		frm.fields_dict.profile_sidebar.$wrapper.find(".upload-btn").on("click", () => {
			new frappe.ui.FileUploader({
				doctype: frm.doctype,
				docname: frm.doc.name,
				on_success(file) {
					if (file.file_url && file.file_url.match(/\.(jpg|jpeg|png|webp)$/i)) {
						frm.set_value("student_image", file.file_url);
						frm.save().then(() => {
							frm.reload_doc();
						});
					}
				},
			});
		});
	},
});
