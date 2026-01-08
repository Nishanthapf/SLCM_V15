frappe.ui.form.on("Student ID Card", {
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Generate Card"), function () {
				frm.call("generate_card").then((r) => {
					frm.refresh();
				});
			});

			if (frm.doc.front_id_image) {
				frm.add_custom_button(__("Print Card"), function () {
					// Open both sides in a print-friendly window
					let front_url = frappe.utils.get_file_link(frm.doc.front_id_image);
					let back_url = frm.doc.back_id_image
						? frappe.utils.get_file_link(frm.doc.back_id_image)
						: null;

					let w = window.open("", "_blank");
					w.document.write(`
						<html>
						<head>
							<title>Print ID Card - ${frm.doc.student_name}</title>
							<style>
								body { margin: 0; padding: 20px; text-align: center; }
								img { max-width: 100%; border: 1px solid #ccc; margin-bottom: 20px; }
								@media print {
									img { page-break-after: always; }
								}
							</style>
						</head>
						<body>
							<img src="${front_url}" />
							${back_url ? `<br><img src="${back_url}" />` : ""}
							<script>
								window.onload = function() { window.print(); }
							</script>
						</body>
						</html>
					`);
					w.document.close();
				});
			}
		}
	},
});
