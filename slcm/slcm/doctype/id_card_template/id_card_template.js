/* global slcm */
frappe.ui.form.on("ID Card Template", {
	refresh(frm) {
		frm.add_custom_button(__("Show Preview"), () => {
			frm.call("get_preview").then((r) => {
				if (!r.message) return;
				// Unhide section
				frm.set_df_property("preview_section", "hidden", 0);
				// Inject HTML
				frm.fields_dict.preview_html.$wrapper.html(r.message);
				// Force repaint
				frm.refresh_field("preview_html");
			});
		});

		frm.trigger("render_editor");
	},

	template_creation_mode(frm) {
		frm.trigger("render_editor");
	},

	card_type(frm) {
		frm.trigger("render_editor");
	},

	render_editor(frm) {
		if (frm.doc.template_creation_mode === "Drag and Drop") {
			new IDCardEditor(frm);
		} else if (frm.doc.template_creation_mode === "Canva") {
			let wrapper = frm.fields_dict.canva_button.$wrapper;
			wrapper.html(`
                <div style="text-align: center; padding: 50px; background: #f0f4f8; border-radius: 8px;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/0/08/Canva_icon_2021.svg" style="width: 64px; margin-bottom: 20px;">
                    <h4>Design with Canva</h4>
                    <p>Create stunning ID cards using Canva's design tools.</p>
                    <button class="btn btn-primary" onclick="window.open('https://www.canva.com', '_blank')">Open Canva</button>
                    <p class="text-muted small mt-2">After designing, export as Image and upload to design assets, or paste HTML if supported.</p>
                </div>
            `);
		}
	},
});

class IDCardEditor {
	constructor(frm) {
		this.frm = frm;
		this.wrapper = frm.fields_dict.canvas_editor.$wrapper;
		this.show_guides = true; // Default to showing guides

		let raw_data = frm.doc.canvas_data;
		if (!raw_data || raw_data === "{}" || raw_data === "[]") {
			this.render_template_selector();
			return;
		} else {
			try {
				let parsed = JSON.parse(raw_data);
				if (Array.isArray(parsed.elements)) {
					this.data = {
						front: parsed.elements,
						back: [],
						orientation: "horizontal",
						bg_color: { front: "#ffffff", back: "#ffffff" },
					};
				} else {
					this.data = parsed;
					if (!this.data.orientation) this.data.orientation = "horizontal";
					if (!this.data.bg_color)
						this.data.bg_color = { front: "#ffffff", back: "#ffffff" };
				}
			} catch (e) {
				this.render_template_selector(); // Fallback
				return;
			}
		}

		this.current_side = "front";
		this.scale = 1.5;
		this.render();
	}

	render_template_selector() {
		// Ensure templates are loaded
		if (typeof slcm === "undefined" || !slcm.templates || !slcm.templates.registry) {
			try {
				frappe.require("/assets/slcm/js/student_id_card_templates.js").then(() => {
					this.render_template_selector();
				});
				return;
			} catch (e) {
				console.error("Templates not found");
			}
		}

		let templates_html = "";
		if (slcm.templates && slcm.templates.registry) {
			templates_html = slcm.templates.registry
				.map((t) => {
					// Generate Preview HTML
					let preview_html = t.front_template_html || "";

					// Replace Jinja/Handlebars tags with placeholders for preview
					preview_html = preview_html
						.replace(/{{ institute_logo }}/g, "https://placehold.co/80x80?text=Logo")
						.replace(
							/{{ passport_size_photo }}/g,
							"https://placehold.co/100x100?text=Photo"
						)
						.replace(/{{ qr_code_image }}/g, "https://placehold.co/80x80?text=QR")
						.replace(
							/{{ authority_signature }}/g,
							"https://placehold.co/60x30?text=Sign"
						)
						.replace(/{{ student_name }}/g, "John Doe")
						.replace(/{{ institute_name }}/g, "Institute Name")
						.replace(/{{.*?}}/g, "..."); // Generic catch-all for other fields

					// Calculate scale and dimensions
					// Vertical: 638x1011
					// Horizontal: 1011x638
					let scale = 0.14;
					let original_w = t.orientation === "Vertical" ? 638 : 1011;
					let original_h = t.orientation === "Vertical" ? 1011 : 638;

					let scaled_w = original_w * scale;
					let scaled_h = original_h * scale;

					let preview_container = `<div style="width: ${scaled_w}px; height: ${scaled_h}px; position: relative; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); background-color: white;">
                                            <div style="width: ${original_w}px; height: ${original_h}px; transform: scale(${scale}); transform-origin: top left; position: absolute; top: 0; left: 0;">
                                                ${preview_html}
                                            </div>
                                         </div>`;

					return `
                 <div class="col-sm-4" style="margin-bottom: 20px;">
                    <div class="tpl-card template-select" data-template="${t.template_id}">
                        <div class="tpl-preview">
                            ${preview_container}
                        </div>
                        <div class="tpl-body">
                            <div class="tpl-title">${t.template_name}</div>
                            <div class="tpl-desc">${t.orientation}</div>
                        </div>
                    </div>
                </div>`;
				})
				.join("");
		}

		this.wrapper.html(`
            <style>
                .tpl-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; transition: all 0.2s; cursor: pointer; background: #fff; height: 100%; position: relative; }
                .tpl-card:hover { border-color: #3498db; transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
                .tpl-preview { height: 160px; background: #f4f6f9; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #eee; position: relative; overflow: hidden; }
                .tpl-body { padding: 20px; text-align: center; }
                .tpl-title { font-weight: bold; font-size: 16px; margin-bottom: 5px; color: #333; }
                .tpl-desc { font-size: 13px; color: #777; line-height: 1.4; }
                .select-container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
            </style>
            <div class="select-container">
                <div style="text-align: center; margin-bottom: 40px;">
                    <h3 style="margin-bottom: 10px;">Select a Template</h3>
                    <p class="text-muted">Choose a starting point.</p>
                </div>
                <div class="row">
                    <!-- Blank Options -->
                    <div class="col-sm-4" style="margin-bottom: 20px;">
                        <div class="tpl-card template-select" data-template="empty">
                            <div class="tpl-preview">
                                <div style="font-size: 40px; color: #ccc;">+</div>
                            </div>
                            <div class="tpl-body">
                                <div class="tpl-title">Blank Canvas</div>
                                <div class="tpl-desc">Start from scratch</div>
                            </div>
                        </div>
                    </div>
                    ${templates_html}
                </div>
            </div>
        `);
		this.wrapper.find(".template-select").on("click", (e) => {
			let t = $(e.currentTarget).closest(".template-select").data("template");
			this.load_default_template(t);
		});
	}

	load_default_template(type) {
		this.data = {
			front: [],
			back: [],
			orientation: "horizontal",
			bg_color: { front: "#ffffff", back: "#ffffff" },
		};

		if (type === "empty") {
			// Already initialized empty
		} else {
			// Fetch from registry
			const tmpl = slcm.templates.get(type);
			if (tmpl) {
				this.data.orientation = tmpl.orientation.toLowerCase();
				// We can't drag&drop the HTML template (it's string).
				// However, the USER's screenshot shows "Drag & Drop Editor"
				// And my templates are "Jinja HTML" templates.
				// This is a conflict: Drag & Drop editor expects a JSON array of elements, not raw HTML string.

				// Solution:
				// If the user selects a "Jinja Template" to start with in "Drag & Drop",
				// we should ideally switch mode OR just put a helpful message?
				// Or, maybe I should convert my HTML templates to "Canvas Data"?
				// That's too complex for now.

				// Alternative: Just set the orientation and maybe a placeholder background?
				// Or better: Let's just create "Canvas Data" representations for my new templates?
				// That's duplication.

				// Re-reading user request: "Refactor... decoupling template handling".
				// The user wants these templates to be available.
				// The "Student ID Card" generation creates a card from a template.
				// The "ID Card Template" editor CREATES a template.

				// So when user selects "Test Visitor ID" in this editor,
				// it should populate the editor with elements that match "Test Visitor ID".

				// Since my templates are defined as HTML, I can't easily convert them to drag-and-drop elements here without parsing.

				// QUICK FIX: For now, I will just set the orientation.
				// Ideally, these presets in the editor should be "Starter Templates" defined as JSON, not HTML.
				// But since I defined them as HTML in `student_id_card_templates.js`...

				// frappe.msgprint(__("Selected template is an HTML Preset. Editor will be set to match orientation, but elements cannot be edited individually."));
				// We could potentially set the background image if available?

				// Wait, if I set 'canvas_data' to null but 'front_html' to the value, maybe it works?
				// But this is the EDITOR. It edits `canvas_data`.

				// For the purpose of "Test Visitor ID", let's just create a basic "Canvas" version of it here manually for the "Test Visitor ID" case,
				// or just acknowledge the limitation.

				// --- MAPPINGS ---

				if (type === "uni_std_vert") {
					// University Standard - Vertical
					this.data.orientation = "vertical";
					this.data.bg_color.front = "#ffffff";

					// Front
					// Header Blue
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 212.5,
						height: 60,
						style: { backgroundColor: "#002147", opacity: 1 },
					});
					// Logo
					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 76,
						y: 5,
						width: 30,
						height: 30,
						style: { opacity: 1, borderRadius: "0" },
					});
					this.data.front.push({
						type: "text",
						mapping: "institute_name",
						content: "[Institute Name]",
						x: 10,
						y: 40,
						style: {
							fontSize: "10px",
							fontWeight: "bold",
							color: "#ffffff",
							textAlign: "center",
							width: "192px",
						},
					});

					// Photo Circle
					this.data.front.push({
						type: "image",
						mapping: "photo",
						content: "/assets/frappe/images/default-avatar.png",
						x: 66,
						y: 80,
						width: 80,
						height: 80,
						style: {
							opacity: 1,
							borderRadius: "50%",
							borderWidth: "4px",
							borderStyle: "solid",
							borderColor: "#f0f0f0",
						},
						shape: "circle",
					});

					// Name & Details
					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Student Name]",
						x: 10,
						y: 170,
						style: {
							fontSize: "14px",
							fontWeight: "bold",
							color: "#333",
							textAlign: "center",
							width: "192px",
						},
					});
					this.data.front.push({
						type: "text",
						mapping: "program",
						content: "[Program]",
						x: 10,
						y: 190,
						style: {
							fontSize: "10px",
							color: "#666",
							textAlign: "center",
							width: "192px",
						},
					});

					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "ID: [Student ID]",
						x: 30,
						y: 220,
						style: { fontSize: "10px", color: "#444" },
					});
					this.data.front.push({
						type: "text",
						mapping: "department",
						content: "Dept: [Department]",
						x: 30,
						y: 235,
						style: { fontSize: "10px", color: "#444" },
					});
					this.data.front.push({
						type: "text",
						mapping: "date_of_birth",
						content: "DOB: [Date of Birth]",
						x: 30,
						y: 250,
						style: { fontSize: "10px", color: "#444" },
					});

					// Footer
					this.data.front.push({
						type: "text",
						content: "STUDENT ID CARD",
						x: 10,
						y: 310,
						style: {
							fontSize: "10px",
							fontWeight: "bold",
							color: "#002147",
							textAlign: "center",
							width: "192px",
						},
					});

					// Back
					this.data.back.push({
						type: "text",
						content: "Terms & Conditions",
						x: 20,
						y: 20,
						style: {
							fontSize: "12px",
							fontWeight: "bold",
							borderBottom: "1px solid #002147",
							color: "#002147",
						},
					});
					this.data.back.push({
						type: "text",
						content: "- This card is property of institute.",
						x: 20,
						y: 45,
						style: { fontSize: "8px" },
					});
					this.data.back.push({
						type: "text",
						content: "- Return if found.",
						x: 20,
						y: 55,
						style: { fontSize: "8px" },
					});

					this.data.back.push({
						type: "text",
						mapping: "phone",
						content: "Emergency: [Phone]",
						x: 20,
						y: 100,
						style: { fontSize: "10px" },
					});
					this.data.back.push({
						type: "text",
						mapping: "blood_group",
						content: "Blood Group: [Blood Group]",
						x: 20,
						y: 115,
						style: { fontSize: "10px" },
					});
					this.data.back.push({
						type: "text",
						mapping: "expiry_date",
						content: "Valid Until: [Expiry Date]",
						x: 20,
						y: 130,
						style: { fontSize: "10px" },
					});

					// Signature & QR
					this.data.back.push({
						type: "image",
						mapping: "authority_signature",
						content: "https://placehold.co/60x30?text=Sign",
						x: 20,
						y: 260,
						width: 50,
						height: 25,
						style: { opacity: 1 },
					});
					this.data.back.push({
						type: "text",
						content: "Registrar",
						x: 20,
						y: 285,
						style: { fontSize: "8px" },
					});

					this.data.back.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/60x60?text=QR",
						x: 100,
						y: 250,
						width: 80,
						height: 80,
						style: { opacity: 1 },
					});
				} else if (type === "uni_std_horiz") {
					// University Standard - Horizontal
					this.data.orientation = "horizontal";
					this.data.bg_color.front = "#ffffff";

					// Left Sidebar Blue
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 116,
						height: 212.5,
						style: { backgroundColor: "#002147", opacity: 1 },
					});

					// Photo
					this.data.front.push({
						type: "image",
						mapping: "photo",
						content: "/assets/frappe/images/default-avatar.png",
						x: 20,
						y: 30,
						width: 75,
						height: 75,
						style: {
							opacity: 1,
							borderRadius: "5px",
							borderWidth: "2px",
							borderStyle: "solid",
							borderColor: "#ffffff",
						},
					});

					this.data.front.push({
						type: "text",
						content: "STUDENT",
						x: 10,
						y: 120,
						style: {
							fontSize: "10px",
							color: "#ffffff",
							opacity: 0.8,
							textAlign: "center",
							width: "96px",
						},
					});
					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "[ID]",
						x: 10,
						y: 135,
						style: {
							fontSize: "14px",
							fontWeight: "bold",
							color: "#ffffff",
							textAlign: "center",
							width: "96px",
						},
					});

					// Right Side content
					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 130,
						y: 15,
						width: 25,
						height: 25,
						style: { opacity: 1 },
					});
					this.data.front.push({
						type: "text",
						mapping: "institute_name",
						content: "[Institute Name]",
						x: 160,
						y: 20,
						style: { fontSize: "14px", fontWeight: "bold", color: "#002147" },
					});

					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Student Name]",
						x: 130,
						y: 60,
						style: { fontSize: "18px", fontWeight: "bold", color: "#333" },
					});
					this.data.front.push({
						type: "text",
						content: "[Program] | [Dept]",
						x: 130,
						y: 85,
						style: { fontSize: "10px", color: "#666", width: "200px" },
					}); // Combined static text approximation

					this.data.front.push({
						type: "text",
						mapping: "expiry_date",
						content: "Valid To: [Expiry Date]",
						x: 130,
						y: 120,
						style: { fontSize: "10px", color: "#444" },
					});

					// Watermark
					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 280,
						y: 160,
						width: 40,
						height: 40,
						style: { opacity: 0.1 },
					});

					// Back
					this.data.back.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 20,
						height: 212.5,
						style: { backgroundColor: "#cecece", opacity: 1 },
					});
					this.data.back.push({
						type: "text",
						content: "INSTRUCTIONS",
						x: 30,
						y: 20,
						style: { fontSize: "12px", fontWeight: "bold" },
					});
					this.data.back.push({
						type: "text",
						content: "Carry always. Report loss.",
						x: 30,
						y: 40,
						style: { fontSize: "10px" },
					});

					this.data.back.push({
						type: "text",
						mapping: "institute_address",
						content: "Addr: [Address]",
						x: 30,
						y: 80,
						style: { fontSize: "10px", width: "150px" },
					});
					this.data.back.push({
						type: "text",
						mapping: "phone",
						content: "Ph: [Phone]",
						x: 30,
						y: 110,
						style: { fontSize: "10px" },
					});

					this.data.back.push({
						type: "image",
						mapping: "authority_signature",
						content: "https://placehold.co/60x30?text=Sign",
						x: 30,
						y: 150,
						width: 50,
						height: 25,
						style: { opacity: 1 },
					});

					// QR Right
					this.data.back.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/100x100?text=QR",
						x: 230,
						y: 50,
						width: 80,
						height: 80,
						style: { opacity: 1 },
					});
					this.data.back.push({
						type: "text",
						content: "Scan to Verify",
						x: 230,
						y: 135,
						style: {
							fontSize: "8px",
							color: "#888",
							textAlign: "center",
							width: "80px",
						},
					});
				} else if (type === "hostel_id") {
					// Hostel ID
					this.data.orientation = "vertical";
					this.data.bg_color.front = "#f4f7f6";

					// Header
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 212.5,
						height: 50,
						style: { backgroundColor: "#2c3e50", opacity: 1 },
					});
					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 10,
						y: 10,
						width: 30,
						height: 30,
						style: { opacity: 1 },
					});
					this.data.front.push({
						type: "text",
						content: "HOSTEL RESIDENT",
						x: 50,
						y: 18,
						style: { fontSize: "14px", fontWeight: "bold", color: "#ffffff" },
					});

					// Photo
					this.data.front.push({
						type: "image",
						mapping: "photo",
						content: "/assets/frappe/images/default-avatar.png",
						x: 56,
						y: 70,
						width: 100,
						height: 100,
						style: { opacity: 1, borderRadius: "10px" },
					});

					// Name
					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Student Name]",
						x: 10,
						y: 190,
						style: {
							fontSize: "16px",
							fontWeight: "bold",
							color: "#2c3e50",
							textAlign: "center",
							width: "192px",
						},
					});
					this.data.front.push({
						type: "text",
						content: "Room: Block B",
						x: 10,
						y: 215,
						style: {
							fontSize: "12px",
							color: "#7f8c8d",
							textAlign: "center",
							width: "192px",
						},
					});

					// Details
					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "ID: [Student ID]",
						x: 20,
						y: 250,
						style: { fontSize: "10px" },
					});
					this.data.front.push({
						type: "text",
						mapping: "blood_group",
						content: "Blood: [Blood Group]",
						x: 20,
						y: 265,
						style: { fontSize: "10px" },
					});
					this.data.front.push({
						type: "text",
						mapping: "phone",
						content: "Emerg: [Phone]",
						x: 20,
						y: 280,
						style: { fontSize: "10px" },
					});

					// Footer Strip
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 327,
						width: 212.5,
						height: 10,
						style: { backgroundColor: "#e74c3c", opacity: 1 },
					});

					// Back
					this.data.back.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/100x100?text=QR",
						x: 56,
						y: 50,
						width: 100,
						height: 100,
						style: { opacity: 1 },
					});
					this.data.back.push({
						type: "text",
						content: "GATE PASS",
						x: 10,
						y: 170,
						style: { fontSize: "16px", textAlign: "center", width: "192px" },
					});
					this.data.back.push({
						type: "text",
						content: "Use for Entry/Exit",
						x: 10,
						y: 195,
						style: { fontSize: "10px", textAlign: "center", width: "192px" },
					});
				} else if (type === "library_card") {
					// Library Card
					this.data.orientation = "horizontal";
					this.data.bg_color.front = "#fffbe7";

					// Border handled by rect? or custom CSS. Just layout elements.
					this.data.front.push({
						type: "rect",
						x: 5,
						y: 5,
						width: 327,
						height: 202.5,
						style: {
							backgroundColor: "transparent",
							opacity: 1,
							borderWidth: "4px",
							borderStyle: "double",
							borderColor: "#5d4037",
						},
					}); // Faux border

					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 20,
						y: 20,
						width: 40,
						height: 40,
						style: { opacity: 1 },
					});

					this.data.front.push({
						type: "text",
						content: "LIBRARY CARD",
						x: 0,
						y: 20,
						style: {
							fontSize: "20px",
							fontWeight: "bold",
							color: "#5d4037",
							textAlign: "center",
							width: "337px",
						},
					});
					this.data.front.push({
						type: "text",
						mapping: "institute_name",
						content: "[Institute Name]",
						x: 0,
						y: 45,
						style: {
							fontSize: "10px",
							fontStyle: "italic",
							textAlign: "center",
							width: "337px",
						},
					});

					// Photo left
					this.data.front.push({
						type: "image",
						mapping: "photo",
						content: "/assets/frappe/images/default-avatar.png",
						x: 30,
						y: 70,
						width: 60,
						height: 75,
						style: {
							opacity: 1,
							borderWidth: "1px",
							borderStyle: "solid",
							borderColor: "#5d4037",
						},
					});

					// Details Right
					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Student Name]",
						x: 110,
						y: 80,
						style: {
							fontSize: "16px",
							fontWeight: "bold",
							color: "#3e2723",
							borderBottom: "1px solid #5d4037",
						},
					});
					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "Mem ID: [Student ID]",
						x: 110,
						y: 110,
						style: { fontSize: "12px" },
					});
					this.data.front.push({
						type: "text",
						mapping: "department",
						content: "Dept: [Department]",
						x: 110,
						y: 130,
						style: { fontSize: "12px" },
					});

					// QR
					this.data.front.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/50x50?text=QR",
						x: 280,
						y: 150,
						width: 40,
						height: 40,
						style: { opacity: 1 },
					});
				} else if (type === "visitor_id") {
					// Visitor ID
					this.data.orientation = "vertical";
					this.data.bg_color.front = "#ffffff";

					// Top Orange Bar
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 212.5,
						height: 20,
						style: { backgroundColor: "#FFAB00", opacity: 1 },
					});

					this.data.front.push({
						type: "text",
						content: "VISITOR",
						x: 10,
						y: 40,
						style: {
							fontSize: "28px",
							color: "#F57C00",
							textAlign: "center",
							width: "192px",
							fontWeight: "bold",
						},
					});
					this.data.front.push({
						type: "text",
						content: "Temporary Pass",
						x: 10,
						y: 70,
						style: {
							fontSize: "12px",
							color: "#666",
							textAlign: "center",
							width: "192px",
						},
					});

					// Box
					this.data.front.push({
						type: "rect",
						x: 20,
						y: 100,
						width: 172.5,
						height: 80,
						style: {
							backgroundColor: "transparent",
							opacity: 1,
							borderWidth: "2px",
							borderStyle: "dashed",
							borderColor: "#ccc",
						},
					});

					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Name]",
						x: 30,
						y: 120,
						style: {
							fontSize: "16px",
							fontWeight: "bold",
							textAlign: "center",
							width: "152px",
						},
					});
					this.data.front.push({
						type: "text",
						content: "Valid for 1 Day",
						x: 30,
						y: 150,
						style: {
							fontSize: "12px",
							color: "#888",
							textAlign: "center",
							width: "152px",
						},
					});

					// QR
					this.data.front.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/100x100?text=QR",
						x: 71,
						y: 200,
						width: 70,
						height: 70,
						style: { opacity: 1 },
					});
				} else if (type === "faculty_id") {
					// Faculty ID - Red Theme
					this.data.orientation = "vertical";
					this.data.bg_color.front = "#ffffff";

					// Header Red
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 212.5,
						height: 60,
						style: { backgroundColor: "#8B0000", opacity: 1 },
					});
					// Logo
					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 76,
						y: 5,
						width: 30,
						height: 30,
						style: { opacity: 1, borderRadius: "0" },
					});
					this.data.front.push({
						type: "text",
						mapping: "institute_name",
						content: "[Institute Name]",
						x: 10,
						y: 40,
						style: {
							fontSize: "10px",
							fontWeight: "bold",
							color: "#ffffff",
							textAlign: "center",
							width: "192px",
						},
					});

					// Photo Square Red Border
					this.data.front.push({
						type: "image",
						mapping: "photo",
						content: "/assets/frappe/images/default-avatar.png",
						x: 66,
						y: 80,
						width: 80,
						height: 80,
						style: {
							opacity: 1,
							borderRadius: "5px",
							borderWidth: "4px",
							borderStyle: "solid",
							borderColor: "#8B0000",
						},
					});

					// Name & Details
					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Faculty Name]",
						x: 10,
						y: 170,
						style: {
							fontSize: "14px",
							fontWeight: "bold",
							color: "#333",
							textAlign: "center",
							width: "192px",
						},
					});
					this.data.front.push({
						type: "text",
						content: "FACULTY",
						x: 10,
						y: 190,
						style: {
							fontSize: "12px",
							fontWeight: "bold",
							color: "#8B0000",
							textAlign: "center",
							width: "192px",
						},
					});

					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "ID: [Employee ID]",
						x: 20,
						y: 220,
						style: { fontSize: "10px", color: "#444" },
					});
					this.data.front.push({
						type: "text",
						mapping: "department",
						content: "Dept: [Department]",
						x: 20,
						y: 235,
						style: { fontSize: "10px", color: "#444" },
					});

					// Footer
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 327,
						width: 212.5,
						height: 10,
						style: { backgroundColor: "#8B0000", opacity: 1 },
					});

					// Back
					this.data.back.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 90,
						y: 20,
						width: 30,
						height: 30,
						style: { opacity: 1 },
					});
					this.data.back.push({
						type: "text",
						content: "Use this card for:",
						x: 20,
						y: 60,
						style: { fontSize: "10px", width: "170px" },
					});
					this.data.back.push({
						type: "text",
						content: "- Campus Access",
						x: 20,
						y: 75,
						style: { fontSize: "10px" },
					});
					this.data.back.push({
						type: "text",
						content: "- Library Privileges",
						x: 20,
						y: 90,
						style: { fontSize: "10px" },
					});

					this.data.back.push({
						type: "text",
						mapping: "phone",
						content: "Emergency: [Phone]",
						x: 20,
						y: 130,
						style: { fontSize: "10px" },
					});
					this.data.back.push({
						type: "text",
						mapping: "blood_group",
						content: "Blood: [Blood Group]",
						x: 20,
						y: 145,
						style: { fontSize: "10px" },
					});

					this.data.back.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/100x100?text=QR",
						x: 66,
						y: 240,
						width: 80,
						height: 80,
						style: { opacity: 1 },
					});
				} else if (type === "driver_id") {
					// Driver ID - Green Theme
					this.data.orientation = "horizontal";
					this.data.bg_color.front = "#ffffff";

					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 337,
						height: 212.5,
						style: {
							backgroundColor: "transparent",
							opacity: 1,
							borderWidth: "4px",
							borderStyle: "solid",
							borderColor: "#336600",
						},
					});

					// Sidebar Green
					this.data.front.push({
						type: "rect",
						x: 0,
						y: 0,
						width: 80,
						height: 212.5,
						style: { backgroundColor: "#336600", opacity: 1 },
					});
					this.data.front.push({
						type: "text",
						content: "DRIVER",
						x: -20,
						y: 100,
						style: {
							fontSize: "16px",
							fontWeight: "bold",
							color: "#ffffff",
							transform: "rotate(-90deg)",
						},
					});

					// Header
					this.data.front.push({
						type: "image",
						mapping: "institute_logo",
						content: "https://placehold.co/60x60?text=LOGO",
						x: 90,
						y: 15,
						width: 30,
						height: 30,
						style: { opacity: 1 },
					});
					this.data.front.push({
						type: "text",
						mapping: "institute_name",
						content: "[Institute Name]",
						x: 130,
						y: 20,
						style: { fontSize: "12px", fontWeight: "bold", color: "#336600" },
					});
					this.data.front.push({
						type: "text",
						content: "Transport Dept",
						x: 130,
						y: 35,
						style: { fontSize: "10px", color: "#555" },
					});

					// Photo Box
					this.data.front.push({
						type: "rect",
						x: 90,
						y: 60,
						width: 70,
						height: 80,
						style: {
							backgroundColor: "#eee",
							opacity: 1,
							borderWidth: "1px",
							borderStyle: "solid",
							borderColor: "#ccc",
						},
					});
					this.data.front.push({
						type: "image",
						mapping: "photo",
						content: "/assets/frappe/images/default-avatar.png",
						x: 92,
						y: 62,
						width: 66,
						height: 76,
						style: { opacity: 1 },
					});

					// Details
					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "[Driver Name]",
						x: 170,
						y: 70,
						style: { fontSize: "16px", fontWeight: "bold", color: "#333" },
					});
					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "ID: [ID]",
						x: 170,
						y: 95,
						style: { fontSize: "12px" },
					});
					this.data.front.push({
						type: "text",
						mapping: "phone",
						content: "[Phone]",
						x: 170,
						y: 110,
						style: { fontSize: "12px" },
					});

					// Back
					this.data.back.push({
						type: "text",
						content: "Vehicle Rules:",
						x: 20,
						y: 20,
						style: { fontSize: "12px", fontWeight: "bold" },
					});
					this.data.back.push({
						type: "text",
						content: "1. Carry card on duty.",
						x: 20,
						y: 40,
						style: { fontSize: "10px" },
					});
					this.data.back.push({
						type: "text",
						content: "2. Follow traffic rules.",
						x: 20,
						y: 55,
						style: { fontSize: "10px" },
					});

					this.data.back.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/100x100?text=QR",
						x: 250,
						y: 150,
						width: 50,
						height: 50,
						style: { opacity: 1 },
					});
				} else if (type === "test_visitor_id") {
					// Manual JSON mapping for Test Visitor ID to demonstrate editor capabilities
					this.data.orientation = "vertical";
					this.data.bg_color.front = "#e0f7fa";

					// Title
					this.data.front.push({
						type: "text",
						content: "TEST VISITOR",
						x: 10,
						y: 40,
						style: {
							fontSize: "24px",
							fontWeight: "bold",
							color: "#006064",
							textAlign: "center",
							width: "192px",
						},
					});
					this.data.front.push({
						type: "text",
						content: "Debugging Template",
						x: 10,
						y: 70,
						style: {
							fontSize: "12px",
							color: "#555",
							textAlign: "center",
							width: "192px",
						},
					});

					// Fields
					this.data.front.push({
						type: "text",
						mapping: "student_name",
						content: "Name: [Student Name]",
						x: 20,
						y: 110,
						style: { fontSize: "14px", fontWeight: "bold" },
					});
					this.data.front.push({
						type: "text",
						mapping: "student_id",
						content: "ID: [Student ID]",
						x: 20,
						y: 130,
						style: { fontSize: "14px" },
					});
					this.data.front.push({
						type: "text",
						mapping: "department",
						content: "Dept: [Department]",
						x: 20,
						y: 150,
						style: { fontSize: "14px" },
					});

					// QR Code
					this.data.front.push({
						type: "image",
						mapping: "qr_code_image",
						content: "https://placehold.co/100x100?text=QR",
						x: 56,
						y: 200,
						width: 100,
						height: 100,
						style: {
							opacity: 1,
							borderWidth: "2px",
							borderStyle: "solid",
							borderColor: "#000",
						},
					});
					this.data.front.push({
						type: "text",
						content: "QR Code Check",
						x: 10,
						y: 310,
						style: { fontSize: "12px", textAlign: "center", width: "192px" },
					});
				}
			}
		}

		this.current_side = "front";
		this.scale = 1.5;
		this.save();
		this.render();
	}

	render() {
		let width, height;
		if (this.data.orientation === "horizontal") {
			width = 337;
			height = 212.5;
		} else {
			width = 212.5;
			height = 337;
		}

		this.wrapper.html(`
            <style>
                .tool-btn { text-align: left; margin-bottom: 5px; }
                .canvas-element { user-select: none; box-sizing: border-box; }
                .canvas-element:hover { outline: 1px dashed #999; }
                .canvas-element.selected { outline: 1px solid blue; }
                .prop-label { font-size: 11px; color: #777; margin-bottom: 2px; display: block; }
            </style>
            <div class="row">
                <div class="col-md-3">
                    <div class="panel panel-default">
                        <div class="panel-heading">Card Settings</div>
                        <div class="panel-body" style="padding: 10px;">
                            <div class="form-group">
                                <label class="prop-label">ORIENTATION</label>
                                <div class="btn-group btn-group-justified btn-group-sm">
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.data.orientation === "horizontal" ? "active" : ""
			}" data-action="set_orientation" data-val="horizontal">Landscape</button>
                                    </div>
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.data.orientation === "vertical" ? "active" : ""
			}" data-action="set_orientation" data-val="vertical">Portrait</button>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="prop-label">ACTIVE SIDE</label>
                                <div class="btn-group btn-group-justified btn-group-sm">
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.current_side === "front" ? "active" : ""
			}" data-side="front">Front</button>
                                    </div>
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.current_side === "back" ? "active" : ""
			}" data-side="back">Back</button>
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
                                <button class="btn btn-danger btn-block btn-sm" id="btn-change-template">
                                    <i class="fa fa-refresh"></i> Reset / Change Template
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="panel panel-default">
                        <div class="panel-heading">Tools</div>
                        <div class="panel-body" style="padding: 10px;">
                            <label class="prop-label">DESIGN</label>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_text">Add Text</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_image">Add Image</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_watermark">Add Watermark</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_shape" data-shape="box">Add Box</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_shape" data-shape="header">Add Header</button>
                             <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_shape" data-shape="footer">Add Footer</button>
                             <div style="margin-top: 5px;">
                                <label class="checkbox-inline" style="font-size: 11px; margin-left: 0;">
                                    <input type="checkbox" id="toggle-guides" ${this.show_guides ? "checked" : ""
			}> Show Guides
                                </label>
                             </div>

                            <hr style="margin: 10px 0;">
                            <label class="prop-label">FIELDS</label>
                            <hr style="margin: 10px 0;">
                            <label class="prop-label">FIELDS</label>
                            ${this.get_field_buttons_html()}

                            <hr style="margin: 10px 0;">
                            <label class="prop-label">INSTITUTE</label>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="institute_logo">Institute Logo</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="authority_signature">Authority Signature</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="institute_name">Institute Name</button>
                             <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="address">Address</button>
                             <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="institute_address">Institute Address</button>
                             <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="department">Department</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div style="margin-bottom: 10px; font-weight: bold; text-align: center;">
                        ${this.current_side.toUpperCase()}
                    </div>
                    <div id="card-canvas-container" style="
                        width: 100%;
                        display: flex;
                        justify-content: center;
                        background: #eee;
                        padding: 20px;
                        border-radius: 12.5px;
                        min-height: 400px;
                        align-items: center;
                    ">

                        <div id="card-canvas-wrapper" style="position: relative;">
                            <div id="card-canvas" style="
                                width: ${width}px;
                                height: ${height}px;
                                background: ${this.data.bg_color[this.current_side] || "#ffffff"};
                                position: relative;
                                overflow: hidden;
                                transform: scale(${this.scale});
                                transform-origin: center center;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                z-index: 10;
                            ">
                            </div>
                            <!-- Alignment Guides Overlay -->
                            <div id="canvas-guides" style="
                                position: absolute; top:0; left:0; pointer-events: none; z-index: 5;
                                width: ${width}px; height: ${height}px;
                                transform: scale(${this.scale}); transform-origin: center center;
                                border: 1px dashed transparent;
                            ">
                                 ${this.show_guides
				? `
                                    <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: rgba(0, 150, 255, 0.5); transform: translateX(-50%);"></div>
                                    <div style="position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: rgba(0, 150, 255, 0.5); transform: translateY(-50%);"></div>
                                 `
				: ""
			}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="panel panel-default">
                         <div class="panel-heading">Properties</div>
                         <div id="element-properties" class="panel-body"></div>
                    </div>
                </div>
            </div>
        `);

		this.canvas = this.wrapper.find("#card-canvas");
		this.properties = this.wrapper.find("#element-properties");
		this.show_properties(-1); // Default view
		this.bind_events();
		this.load_elements();
	}

	get_field_buttons_html() {
		let type = this.frm.doc.card_type || "Student";
		let fields = [];

		// Common Fields
		let common = [
			{ label: "QR Code", field: "qr_code_image" },
			{ label: "Issue Date", field: "issue_date" },
			{ label: "Expiry Date", field: "expiry_date" },
		];

		if (type === "Student") {
			fields = [
				{ label: "Student Name", field: "student_name" },
				{ label: "Student Photo", field: "photo" },
				{ label: "Student ID", field: "student_id" },
				{ label: "Blood Group", field: "blood_group" },
				{ label: "Date of Birth", field: "date_of_birth" },
				{ label: "Academic Year", field: "academic_year" },
				{ label: "Program", field: "program" },
				{ label: "Department", field: "department" },
				{ label: "Email", field: "email" },
				{ label: "Phone", field: "phone" },
				{ label: "Address", field: "address" },
			];
		} else if (type === "Faculty") {
			fields = [
				{ label: "Faculty Name", field: "student_name", content: "[Faculty Name]" },
				{ label: "Photo", field: "photo" },
				{ label: "Employee ID", field: "student_id", content: "[Employee ID]" },
				{ label: "Designation", field: "designation", content: "[Designation]" },
				{ label: "Department", field: "department" },
				{ label: "Email", field: "email" },
				{ label: "Phone", field: "phone" },
				{ label: "Blood Group", field: "blood_group" },
			];
		} else if (type === "Driver") {
			fields = [
				{ label: "Driver Name", field: "student_name", content: "[Driver Name]" },
				{ label: "Photo", field: "photo" },
				{ label: "Driver ID", field: "student_id", content: "[Driver ID]" },
				{ label: "License No", field: "license_number", content: "[License No]" },
				{ label: "Phone", field: "phone" },
				{ label: "Blood Group", field: "blood_group" },
			];
		} else if (type === "Visitor") {
			fields = [
				{ label: "Visitor Name", field: "student_name", content: "[Visitor Name]" },
				{ label: "Company", field: "visitor_company", content: "[Company]" },
				{ label: "Phone", field: "phone" },
				{ label: "Purpose", field: "purpose", content: "[Purpose]" },
			];
		} else if (type === "Non-Faculty") {
			fields = [
				{ label: "Staff Name", field: "student_name", content: "[Staff Name]" },
				{ label: "Designation", field: "designation", content: "[Designation]" },
				{ label: "Department", field: "department" },
				{ label: "Company", field: "visitor_company", content: "[Company]" },
				{ label: "Email", field: "email" },
				{ label: "Phone", field: "phone" },
			];
		}

		// Merge common
		fields = fields.concat(common);

		return fields
			.map((f) => {
				let contentAttr = f.content ? `data-content="${f.content}"` : "";
				return `<button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="${f.field}" ${contentAttr}>${f.label}</button>`;
			})
			.join("");
	}

	bind_events() {
		this.wrapper.find('[data-action="set_orientation"]').on("click", (e) => {
			this.data.orientation = $(e.target).data("val");
			this.save();
			this.render();
		});

		this.wrapper.find("#btn-change-template").on("click", () => {
			frappe.confirm(
				"Are you sure you want to change the template? This will discard your current design and unsaved changes.",
				() => {
					this.data = {
						front: [],
						back: [],
						orientation: "horizontal",
						bg_color: { front: "#ffffff", back: "#ffffff" },
					};
					this.save();
					this.render_template_selector();
				}
			);
		});

		this.wrapper.find("[data-side]").on("click", (e) => {
			e.preventDefault();
			this.current_side = $(e.target).data("side");
			this.render();
		});

		this.wrapper.find('[data-action="add_text"]').on("click", () => {
			this.add_element({
				type: "text",
				content: "New Text",
				x: 20,
				y: 50,
				style: {
					fontSize: "12px",
					fontWeight: "normal",
					color: "#000000",
					fontFamily: "Arial",
					opacity: 1,
				},
			});
		});

		this.wrapper.find('[data-action="add_image"]').on("click", () => {
			this.add_element({
				type: "image",
				content: "https://placehold.co/100x100",
				x: 20,
				y: 50,
				width: 50,
				height: 50,
				style: { opacity: 1 },
			});
		});

		this.wrapper.find('[data-action="add_watermark"]').on("click", () => {
			let w = this.data.orientation === "horizontal" ? 337 : 212.5;
			let h = this.data.orientation === "horizontal" ? 212.5 : 337;
			let img =
				this.frm.doc.watermark_image || "https://placehold.co/200x200?text=Watermark";
			this.add_element(
				{
					type: "image",
					content: img,
					x: (w - 150) / 2,
					y: (h - 150) / 2,
					width: 150,
					height: 150,
					style: { opacity: 0.2 },
				},
				true
			); // Send to back
		});

		this.wrapper.find('[data-action="add_shape"]').on("click", (e) => {
			let shape = $(e.target).data("shape");
			let w = this.data.orientation === "horizontal" ? 337 : 212.5;
			let h = this.data.orientation === "horizontal" ? 212.5 : 337;
			let el = { type: "rect", style: { backgroundColor: "#3498db", opacity: 1 } };

			if (shape === "header") {
				el.x = 0;
				el.y = 0;
				el.width = w;
				el.height = 40;
			} else if (shape === "footer") {
				el.x = 0;
				el.y = h - 40;
				el.width = w;
				el.height = 40;
			} else {
				el.x = 20;
				el.y = 20;
				el.width = 100;
				el.height = 50;
			}
			this.add_element(el);
		});

		this.wrapper.find('[data-action="add_field"]').on("click", (e) => {
			let field = $(e.currentTarget).data("field");
			let el = { x: 20, y: 50, style: { opacity: 1 } };
			if (
				["photo", "institute_logo", "authority_signature", "qr_code_image"].includes(field)
			) {
				el.type = "image";
				el.mapping = field;
				el.width = 60;
				el.height = 60;
				if (field === "photo") el.content = "/assets/frappe/images/default-avatar.png";
				else if (field === "qr_code_image")
					el.content = "https://placehold.co/60x60?text=QR";
				else el.content = "https://placehold.co/60x60?text=IMG";
			} else {
				el.type = "text";
				el.mapping = field;
				let customContent = $(e.currentTarget).data("content");
				el.content = customContent ? customContent : `[${$(e.currentTarget).text()}]`;
				el.style.fontSize = "12px";
				el.style.fontWeight = "bold";
				el.style.color = "#000000";
			}
			this.add_element(el);
		});

		this.wrapper.find("#toggle-guides").on("change", (e) => {
			this.show_guides = $(e.target).is(":checked");
			this.render();
		});
	}

	add_element(el_data, send_to_back) {
		if (!this.data[this.current_side]) this.data[this.current_side] = [];
		if (send_to_back) {
			this.data[this.current_side].unshift(el_data);
			this.render_element(el_data, 0);
		} else {
			this.data[this.current_side].push(el_data);
			this.render_element(el_data, this.data[this.current_side].length - 1);
		}
		this.save();
		this.load_elements(); // Reload to correct z-index
	}

	load_elements() {
		this.canvas.empty();
		let elements = this.data[this.current_side] || [];
		elements.forEach((el, index) => {
			this.render_element(el, index);
		});
	}

	render_element(el, index) {
		let el_dom;
		let opacity = el.style && el.style.opacity !== undefined ? el.style.opacity : 1;

		if (el.type === "text") {
			el_dom = $(
				`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; white-space: nowrap;">${el.content}</div>`
			);
			if (el.style) el_dom.css(el.style);
		} else if (el.type === "image") {
			el_dom =
				$(`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; width: ${el.width}px; height: ${el.height}px; opacity: ${opacity}; overflow: hidden;">
                <img src="${el.content}" style="width: 100%; height: 100%; object-fit: cover; pointer-events: none;">
            </div>`);
			if (el.style) el_dom.css(el.style);
		} else if (el.type === "rect") {
			el_dom = $(
				`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; width: ${el.width}px; height: ${el.height}px;"></div>`
			);
			if (el.style) el_dom.css(el.style);
		}

		el_dom.on("mousedown", (e) => {
			e.preventDefault();
			e.stopPropagation();
			this.select_element(index, el_dom);
			let startX = e.clientX,
				startY = e.clientY;
			let elemLeft = el.x,
				elemTop = el.y;

			let moveHandler = (moveEvent) => {
				let dx = (moveEvent.clientX - startX) / this.scale;
				let dy = (moveEvent.clientY - startY) / this.scale;
				el.x = elemLeft + dx;
				el.y = elemTop + dy;
				el_dom.css({ left: el.x + "px", top: el.y + "px" });
			};
			let upHandler = () => {
				$(document).off("mousemove", moveHandler);
				$(document).off("mouseup", upHandler);
				this.save();
				this.show_properties(index);
			};
			$(document).on("mousemove", moveHandler);
			$(document).on("mouseup", upHandler);
		});
		this.canvas.append(el_dom);
	}

	select_element(index, dom) {
		this.canvas.find(".canvas-element").removeClass("selected");
		dom.addClass("selected");
		this.show_properties(index);
	}

	show_properties(index) {
		if (index === -1 || !this.data[this.current_side][index]) {
			// Global Properties
			this.properties.html(`
               <div class="form-group">
                    <label class="prop-label">CANVAS BACKGROUND</label>
                    <input type="color" class="form-control input-sm global-bg-change" value="${this.data.bg_color[this.current_side] || "#ffffff"
				}">
               </div>
               <p class="text-muted text-center" style="margin-top: 20px;">Select an element to edit.</p>
             `);
			this.wrapper.find(".global-bg-change").on("change", (e) => {
				this.data.bg_color[this.current_side] = $(e.target).val();
				this.save();
				this.render();
			});
			return;
		}

		let el = this.data[this.current_side][index];
		let opacity = el.style && el.style.opacity !== undefined ? el.style.opacity : 1;

		let html = `
            <div class="row">
                <div class="col-xs-6">
                     <label class="prop-label">X POS</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="x" value="${Math.round(
			el.x
		)}">
                </div>
                <div class="col-xs-6">
                     <label class="prop-label">Y POS</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="y" value="${Math.round(
			el.y
		)}">
                </div>
            </div>
        `;

		if (el.type === "rect" || el.type === "image") {
			html += `
            <div class="row" style="margin-top: 5px;">
                <div class="col-xs-6">
                     <label class="prop-label">WIDTH</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="width" value="${Math.round(
				el.width
			)}">
                </div>
                <div class="col-xs-6">
                     <label class="prop-label">HEIGHT</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="height" value="${Math.round(
				el.height
			)}">
                </div>
            </div>`;

			if (el.type === "image") {
				html += `
                <div style="margin-top: 10px;">
                    <label class="prop-label">SHAPE</label>
                    <select class="form-control input-sm shape-change">
                        <option value="rect" ${!el.shape || el.shape === "rect" ? "selected" : ""
					}>Rectangle</option>
                        <option value="circle" ${el.shape === "circle" ? "selected" : ""
					}>Circle</option>
                        <option value="triangle" ${el.shape === "triangle" ? "selected" : ""
					}>Triangle</option>
                    </select>
                </div>`;
			}

			// Border Controls for Rect and Image
			let bs = el.border_settings || {
				style: "none",
				width: 1,
				color: "#000000",
				top: false,
				bottom: false,
				left: false,
				right: false,
			};
			html += `
            <div style="margin-top: 10px; background: #f9f9f9; padding: 5px; border: 1px solid #ddd;">
                <label class="prop-label">BORDER</label>
                <div class="row">
                    <div class="col-xs-6">
                        <label class="prop-label" style="font-weight:normal">Style</label>
                        <select class="form-control input-sm border-change" data-key="style">
                            <option value="none" ${bs.style === "none" ? "selected" : ""
				}>None</option>
                            <option value="solid" ${bs.style === "solid" ? "selected" : ""
				}>Solid</option>
                            <option value="double" ${bs.style === "double" ? "selected" : ""
				}>Double</option>
                            <option value="dashed" ${bs.style === "dashed" ? "selected" : ""
				}>Dashed</option>
                        </select>
                    </div>
                    <div class="col-xs-6">
                        <label class="prop-label" style="font-weight:normal">Width (px)</label>
                        <input type="number" class="form-control input-sm border-change" data-key="width" value="${bs.width
				}">
                    </div>
                </div>
                <div class="row" style="margin-top: 5px;">
                    <div class="col-xs-12">
                        <label class="prop-label" style="font-weight:normal">Color</label>
                        <input type="color" class="form-control input-sm border-change" data-key="color" value="${bs.color
				}">
                    </div>
                </div>
                <div class="row" style="margin-top: 5px;">
                    <div class="col-xs-12">
                        <label class="prop-label" style="font-weight:normal">Sides</label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                            <input type="checkbox" class="border-change" data-key="top" ${bs.top ? "checked" : ""
				}> Top
                        </label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                             <input type="checkbox" class="border-change" data-key="bottom" ${bs.bottom ? "checked" : ""
				}> Bot
                        </label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                             <input type="checkbox" class="border-change" data-key="left" ${bs.left ? "checked" : ""
				}> Left
                        </label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                             <input type="checkbox" class="border-change" data-key="right" ${bs.right ? "checked" : ""
				}> Right
                        </label>
                    </div>
                </div>
            </div>`;
		}

		html += `<div style="margin-top: 10px;">
             <label class="prop-label">OPACITY (${opacity})</label>
             <input type="range" class="style-change" data-style="opacity" min="0" max="1" step="0.1" value="${opacity}" style="width:100%">
        </div>`;

		html += `<div style="margin-top: 10px; display: flex; gap: 5px;">
            <button class="btn btn-default btn-xs flex-grow tool-action" data-tool="center_h" title="Center Horizontal"><i class="fa fa-arrows-h"></i> Center H</button>
            <button class="btn btn-default btn-xs flex-grow tool-action" data-tool="center_v" title="Center Vertical"><i class="fa fa-arrows-v"></i> Center V</button>
        </div>`;

		html += `<div style="margin-top: 5px; display: flex; gap: 5px;">
            <button class="btn btn-default btn-xs flex-grow tool-action" data-tool="bring_front" title="Bring to Front"><i class="fa fa-level-up"></i> Front</button>
            <button class="btn btn-default btn-xs flex-grow tool-action" data-tool="send_back" title="Send to Back"><i class="fa fa-level-down"></i> Back</button>
        </div>`;

		if (el.type === "text") {
			html += `<hr style="margin: 10px 0;">
                <label class="prop-label">TEXT CONTENT</label>
                <input type="text" class="form-control input-sm prop-change" data-prop="content" value="${el.content
				}" ${el.mapping ? "readonly" : ""}>
                <div class="row" style="margin-top:5px;">
                    <div class="col-xs-6">
                        <label class="prop-label">SIZE</label>
                        <input type="text" class="form-control input-sm style-change" data-style="fontSize" value="${el.style.fontSize
				}">
                    </div>
                    <div class="col-xs-6">
                        <label class="prop-label">COLOR</label>
                        <input type="color" class="form-control input-sm style-change" data-style="color" value="${el.style.color
				}">
                    </div>
                </div>`;
		} else if (el.type === "rect") {
			html += `<hr style="margin: 10px 0;">
                <label class="prop-label">FILL COLOR</label>
                <input type="color" class="form-control input-sm style-change" data-style="backgroundColor" value="${el.style.backgroundColor}">`;
		}

		html += `<hr><button class="btn btn-danger btn-sm btn-block remove-el">Internal Remove</button>`;

		this.properties.html(html);
		this.bind_property_events(index);
	}

	bind_property_events(index) {
		let el = this.data[this.current_side][index];

		this.properties.find(".prop-change").on("change", (e) => {
			let prop = $(e.target).data("prop");
			let val = $(e.target).val();
			if (["x", "y", "width", "height"].includes(prop)) val = parseFloat(val);
			el[prop] = val;
			this.load_elements();
			this.canvas.find(`[data-index="${index}"]`).addClass("selected");
			this.save();
		});

		this.properties.find(".style-change").on("input change", (e) => {
			let style = $(e.target).data("style");
			let val = $(e.target).val();
			if (!el.style) el.style = {};
			el.style[style] = val;
			this.load_elements();
			this.canvas.find(`[data-index="${index}"]`).addClass("selected");
			this.save();
			// Live update opacity label
			if (style === "opacity") $(e.target).prev().text(`OPACITY (${val})`);
		});

		this.properties.find(".tool-action").on("click", (e) => {
			let tool = $(e.currentTarget).data("tool");
			let w_canvas = this.data.orientation === "horizontal" ? 337 : 212.5;
			let h_canvas = this.data.orientation === "horizontal" ? 212.5 : 337;

			if (tool === "center_h") {
				el.x =
					(w_canvas -
						(el.width || $(this.canvas.find(`[data-index="${index}"]`)).width())) /
					2;
			} else if (tool === "center_v") {
				el.y =
					(h_canvas -
						(el.height || $(this.canvas.find(`[data-index="${index}"]`)).height())) /
					2;
			} else if (tool === "bring_front") {
				this.data[this.current_side].splice(index, 1);
				this.data[this.current_side].push(el);
				this.save();
				this.load_elements();
				return; // Index changed
			} else if (tool === "send_back") {
				this.data[this.current_side].splice(index, 1);
				this.data[this.current_side].unshift(el);
				this.save();
				this.load_elements();
				return; // Index changed
			}
			this.load_elements();
			this.canvas.find(`[data-index="${index}"]`).addClass("selected");
			this.save();
		});

		this.properties.find(".remove-el").on("click", () => {
			this.data[this.current_side].splice(index, 1);
			this.show_properties(-1);
			this.load_elements();
			this.save();
		});

		// Shape Handler
		this.properties.find(".shape-change").on("change", (e) => {
			let shape = $(e.target).val();
			el.shape = shape;
			if (!el.style) el.style = {};

			if (shape === "circle") {
				el.style.borderRadius = "50%";
				el.style.clipPath = "none";
			} else if (shape === "triangle") {
				el.style.borderRadius = "0";
				el.style.clipPath = "polygon(50% 0%, 0% 100%, 100% 100%)";
			} else {
				el.style.borderRadius = "0";
				el.style.clipPath = "none";
			}
			this.load_elements();
			this.canvas.find(`[data-index="${index}"]`).addClass("selected");
			this.save();
		});

		// Border Handler
		this.properties.find(".border-change").on("change input", (e) => {
			let key = $(e.target).data("key");
			let val;
			if ($(e.target).attr("type") === "checkbox") {
				val = $(e.target).is(":checked");
			} else {
				val = $(e.target).val();
			}

			if (!el.border_settings)
				el.border_settings = {
					style: "none",
					width: 1,
					color: "#000000",
					top: false,
					bottom: false,
					left: false,
					right: false,
				};
			el.border_settings[key] = val;

			if (!el.style) el.style = {};

			// Helper to apply per-side props
			const sides = ["top", "bottom", "left", "right"];
			const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

			sides.forEach((side) => {
				if (el.border_settings[side] && el.border_settings.style !== "none") {
					el.style[`border${cap(side)}Style`] = el.border_settings.style;
					el.style[`border${cap(side)}Width`] = el.border_settings.width + "px";
					el.style[`border${cap(side)}Color`] = el.border_settings.color;
				} else {
					el.style[`border${cap(side)}Style`] = "none";
					el.style[`border${cap(side)}Width`] = "0px";
				}
			});

			this.load_elements();
			this.canvas.find(`[data-index="${index}"]`).addClass("selected");
			this.save();
		});
	}

	save() {
		this.frm.set_value("canvas_data", JSON.stringify(this.data));
	}
}
