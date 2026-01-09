
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

        frm.trigger('render_editor');
    },

    template_creation_mode(frm) {
        frm.trigger('render_editor');
    },

    render_editor(frm) {
        if (frm.doc.template_creation_mode === 'Drag and Drop') {
            new IDCardEditor(frm);
        } else if (frm.doc.template_creation_mode === 'Canva') {
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
    }
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
                    this.data = { front: parsed.elements, back: [], orientation: 'horizontal', bg_color: { front: '#ffffff', back: '#ffffff' } };
                } else {
                    this.data = parsed;
                    if (!this.data.orientation) this.data.orientation = 'horizontal';
                    if (!this.data.bg_color) this.data.bg_color = { front: '#ffffff', back: '#ffffff' };
                }
            } catch (e) {
                this.render_template_selector(); // Fallback
                return;
            }
        }

        this.current_side = 'front';
        this.scale = 1.5;
        this.render();
    }

    render_template_selector() {
        this.wrapper.html(`
            <style>
                .tpl-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; transition: all 0.2s; cursor: pointer; background: #fff; height: 100%; position: relative; }
                .tpl-card:hover { border-color: #3498db; transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }
                .tpl-preview { height: 160px; background: #f4f6f9; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #eee; position: relative; overflow: hidden; }
                .tpl-body { padding: 20px; text-align: center; }
                .tpl-title { font-weight: bold; font-size: 16px; margin-bottom: 5px; color: #333; }
                .tpl-desc { font-size: 13px; color: #777; line-height: 1.4; }
                
                /* Mini Previews - Pure CSS */
                .mini-card { background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.15); position: relative; overflow: hidden; }
                
                /* College Mini */
                .mini-college { width: 60px; height: 96px; border-radius: 4px; }
                .mini-college .header { background: #1a4d80; height: 20px; width: 100%; margin-bottom: 8px; }
                .mini-college .photo { width: 24px; height: 24px; border: 1px solid #ddd; background: #eee; margin: 0 auto 5px; border-radius: 50%; }
                .mini-college .lines { display: flex; flex-direction: column; gap: 3px; align-items: center; }
                .mini-line { height: 2px; background: #e0e0e0; border-radius: 1px; }

                /* University Mini */
                .mini-uni { width: 96px; height: 60px; border-radius: 4px; display: flex; }
                .mini-uni .side { width: 24px; height: 100%; background: #800000; }
                .mini-uni .main { flex: 1; padding: 6px; display: flex; flex-direction: column; gap: 4px; }
                .mini-uni .photo { width: 16px; height: 16px; background: #eee; border-radius: 50%; border: 1px solid #fff; position: absolute; left: 4px; top: 8px; }

                /* Empty Mini */
                .mini-empty { width: 60px; height: 96px; border: 1px dashed #ccc; border-radius: 4px; display: flex; align-items: center; justify-content: center; }
                
                .select-container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
            </style>
            <div class="select-container">
                <div style="text-align: center; margin-bottom: 40px;">
                    <h3 style="margin-bottom: 10px;">Select a Template</h3>
                    <p class="text-muted">Choose a starting point for your ID card design.</p>
                </div>
                <div class="row">
                    <div class="col-sm-4">
                        <div class="tpl-card template-select" data-template="empty">
                            <div class="tpl-preview">
                                <div class="mini-card mini-empty">
                                    <i class="fa fa-plus" style="color: #ccc;"></i>
                                </div>
                            </div>
                            <div class="tpl-body">
                                <div class="tpl-title">Blank Canvas</div>
                                <div class="tpl-desc">Start from scratch with a completely empty canvas.</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-4">
                        <div class="tpl-card template-select" data-template="college">
                            <div class="tpl-preview">
                                <div class="mini-card mini-college">
                                    <div class="header"></div>
                                    <div class="photo"></div>
                                    <div class="lines">
                                        <div class="mini-line" style="width: 30px;"></div>
                                        <div class="mini-line" style="width: 20px;"></div>
                                         <div class="mini-line" style="width: 25px; margin-top: 5px;"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="tpl-body">
                                <div class="tpl-title">College Style</div>
                                <div class="tpl-desc">Vertical layout ideal for colleges. Features a header bar and centered student photo.</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-sm-4">
                        <div class="tpl-card template-select" data-template="university">
                            <div class="tpl-preview">
                                <div class="mini-card mini-uni">
                                    <div class="side"></div>
                                    <div class="photo"></div>
                                    <div class="main">
                                        <div class="mini-line" style="width: 40px; background: #ccc;"></div>
                                        <div class="mini-line" style="width: 30px;"></div>
                                        <div class="mini-line" style="width: 35px;"></div>
                                        <div class="mini-line" style="width: 20px; margin-top: auto;"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="tpl-body">
                                <div class="tpl-title">University Style</div>
                                <div class="tpl-desc">Professional horizontal layout with a side strip and aligned details.</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        this.wrapper.find('.template-select').on('click', (e) => {
            let t = $(e.currentTarget).closest('.template-select').data('template');
            this.load_default_template(t);
        });
    }

    load_default_template(type) {
        this.data = { front: [], back: [], orientation: 'horizontal', bg_color: { front: '#ffffff', back: '#ffffff' } };

        if (type === 'college') {
            // College Style: Simple, Header Bar, Photo Left
            this.data.orientation = 'vertical';
            this.data.front = [
                // Header
                { type: 'rect', x: 0, y: 0, width: 212.5, height: 60, style: { backgroundColor: '#1a4d80', opacity: 1 } },
                // Institute Logo (Top Center)
                { type: 'image', mapping: 'institute_logo', content: 'https://placehold.co/60x60?text=LOGO', x: 76, y: 5, width: 60, height: 60, style: { opacity: 1, borderRadius: '50%' }, shape: 'circle' },
                // Institute Name
                { type: 'text', mapping: 'institute_name', content: '[Institute Name]', x: 10, y: 70, style: { fontSize: '14px', fontWeight: 'bold', color: '#1a4d80', textAlign: 'center', width: '192px' } },
                // Photo
                { type: 'image', mapping: 'photo', content: '/assets/frappe/images/default-avatar.png', x: 71, y: 100, width: 70, height: 70, style: { opacity: 1, borderRadius: '5px', borderWidth: '1px', borderStyle: 'solid', borderColor: '#ccc' } },
                // Name
                { type: 'text', mapping: 'student_name', content: '[Student Name]', x: 10, y: 180, style: { fontSize: '12px', fontWeight: 'bold', color: '#000000', textAlign: 'center', width: '192px' } },
                // Program
                { type: 'text', mapping: 'program', content: '[Program]', x: 10, y: 195, style: { fontSize: '10px', fontWeight: 'normal', color: '#555', textAlign: 'center', width: '192px' } },
                // Details
                { type: 'text', mapping: 'student_id', content: 'ID: [Student ID]', x: 20, y: 220, style: { fontSize: '10px', color: '#000000' } },
                { type: 'text', mapping: 'blood_group', content: 'Blood Group: [Blood Group]', x: 20, y: 235, style: { fontSize: '10px', color: '#000000' } },
                // Footer Elements
                { type: 'image', mapping: 'qr_code_image', content: 'https://placehold.co/50x50?text=QR', x: 10, y: 280, width: 50, height: 50, style: { opacity: 1 } },
                { type: 'image', mapping: 'authority_signature', content: 'https://placehold.co/60x30?text=Sign', x: 140, y: 290, width: 60, height: 30, style: { opacity: 1 } },
                { type: 'text', content: 'Authority Signature', x: 135, y: 320, style: { fontSize: '8px', color: '#555' } }
            ];
            // College Back
            this.data.back = [
                { type: 'text', content: 'Instructions', x: 10, y: 20, style: { fontSize: '12px', fontWeight: 'bold', textDecoration: 'underline' } },
                { type: 'text', content: '1. This card is non-transferable.', x: 10, y: 40, style: { fontSize: '10px' } },
                { type: 'text', content: '2. Report loss immediately.', x: 10, y: 55, style: { fontSize: '10px' } },
                { type: 'text', content: 'If found, please return to:', x: 10, y: 80, style: { fontSize: '10px', fontWeight: 'bold' } },
                { type: 'text', mapping: 'institute_address', content: '[Institute Address]', x: 10, y: 95, style: { fontSize: '10px', width: '190px' } },
                { type: 'text', content: 'Emergency Contact:', x: 10, y: 150, style: { fontSize: '10px', fontWeight: 'bold' } },
                { type: 'text', mapping: 'phone', content: '[Phone]', x: 10, y: 165, style: { fontSize: '10px' } }
            ];
        } else if (type === 'university') {
            // University Style: Horizontal, Sidebar, Professional
            this.data.orientation = 'horizontal';
            this.data.front = [
                // Sidebar
                { type: 'rect', x: 0, y: 0, width: 80, height: 212.5, style: { backgroundColor: '#800000', opacity: 1 } },
                // Photo
                { type: 'image', mapping: 'photo', content: '/assets/frappe/images/default-avatar.png', x: 10, y: 20, width: 60, height: 60, style: { opacity: 1, borderRadius: '50%', borderWidth: '2px', borderStyle: 'solid', borderColor: '#fff' }, shape: 'circle' },
                // ID in Sidebar
                { type: 'text', mapping: 'student_id', content: '[Student ID]', x: 5, y: 90, style: { fontSize: '10px', fontWeight: 'bold', color: '#ffffff', textAlign: 'center', width: '70px' } },

                // Main Content
                // Logo
                { type: 'image', mapping: 'institute_logo', content: 'https://placehold.co/50x50?text=LOGO', x: 280, y: 10, width: 40, height: 40, style: { opacity: 1 } },

                // Institute Name
                { type: 'text', mapping: 'institute_name', content: '[Institute Name]', x: 90, y: 15, style: { fontSize: '16px', fontWeight: 'bold', color: '#800000' } },
                { type: 'text', mapping: 'institute_address', content: '[Institute Address]', x: 90, y: 35, style: { fontSize: '8px', color: '#555' } },

                // Student Details
                { type: 'text', mapping: 'student_name', content: '[Student Name]', x: 90, y: 70, style: { fontSize: '14px', fontWeight: 'bold', color: '#000000' } },
                { type: 'text', mapping: 'program', content: '[Program]', x: 90, y: 90, style: { fontSize: '10px', color: '#555' } },
                { type: 'text', mapping: 'email', content: 'E: [Email]', x: 90, y: 110, style: { fontSize: '10px', color: '#000000' } },
                { type: 'text', mapping: 'phone', content: 'P: [Phone]', x: 90, y: 125, style: { fontSize: '10px', color: '#000000' } },

                // Bottom
                { type: 'image', mapping: 'qr_code_image', content: 'https://placehold.co/50x50?text=QR', x: 270, y: 150, width: 40, height: 40, style: { opacity: 1 } },
                { type: 'image', mapping: 'authority_signature', content: 'https://placehold.co/60x30?text=Sign', x: 90, y: 160, width: 60, height: 30, style: { opacity: 1 } }
            ];
            // University Back
            this.data.back = [
                { type: 'rect', x: 0, y: 0, width: 337.5, height: 30, style: { backgroundColor: '#800000', opacity: 1 } },
                { type: 'text', content: 'TERMS & CONDITIONS', x: 10, y: 8, style: { fontSize: '10px', fontWeight: 'bold', color: '#ffffff' } },
                { type: 'text', content: 'This card is the property of the University.', x: 10, y: 40, style: { fontSize: '10px' } },
                { type: 'text', content: 'If found, please return to:', x: 10, y: 60, style: { fontSize: '10px', fontWeight: 'bold' } },
                { type: 'text', mapping: 'institute_address', content: '[Address]', x: 10, y: 75, style: { fontSize: '10px', width: '300px' } },
                { type: 'image', content: 'https://placehold.co/150x50?text=BARCODE', x: 93, y: 140, width: 150, height: 50, style: { opacity: 0.8 } }
            ];
        }

        this.current_side = 'front';
        this.scale = 1.5;
        this.save();
        this.render();
    }

    render() {
        let width, height;
        if (this.data.orientation === 'horizontal') {
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
                                        <button class="btn btn-default ${this.data.orientation === 'horizontal' ? 'active' : ''}" data-action="set_orientation" data-val="horizontal">Landscape</button>
                                    </div>
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.data.orientation === 'vertical' ? 'active' : ''}" data-action="set_orientation" data-val="vertical">Portrait</button>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <label class="prop-label">ACTIVE SIDE</label>
                                <div class="btn-group btn-group-justified btn-group-sm">
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.current_side === 'front' ? 'active' : ''}" data-side="front">Front</button>
                                    </div>
                                    <div class="btn-group">
                                        <button class="btn btn-default ${this.current_side === 'back' ? 'active' : ''}" data-side="back">Back</button>
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
                                    <input type="checkbox" id="toggle-guides" ${this.show_guides ? 'checked' : ''}> Show Guides
                                </label>
                             </div>
                            
                            <hr style="margin: 10px 0;">
                            <label class="prop-label">FIELDS</label>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="student_name">Student Name</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="photo">Student Photo</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="student_id">Student ID</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="blood_group">Blood Group</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="qr_code_image">QR Code</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="date_of_birth">Date of Birth</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="academic_year">Academic Year</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="program">Program</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="email">Email</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="phone">Phone</button>
                            
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
                                background: ${this.data.bg_color[this.current_side] || '#ffffff'};
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
                                 ${this.show_guides ? `
                                    <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: rgba(0, 150, 255, 0.5); transform: translateX(-50%);"></div>
                                    <div style="position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: rgba(0, 150, 255, 0.5); transform: translateY(-50%);"></div>
                                 ` : ''}
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

        this.canvas = this.wrapper.find('#card-canvas');
        this.properties = this.wrapper.find('#element-properties');
        this.show_properties(-1); // Default view
        this.bind_events();
        this.load_elements();
    }

    bind_events() {
        this.wrapper.find('[data-action="set_orientation"]').on('click', (e) => {
            this.data.orientation = $(e.target).data('val');
            this.save();
            this.render();
        });

        this.wrapper.find('#btn-change-template').on('click', () => {
            frappe.confirm(
                'Are you sure you want to change the template? This will discard your current design and unsaved changes.',
                () => {
                    this.data = { front: [], back: [], orientation: 'horizontal', bg_color: { front: '#ffffff', back: '#ffffff' } };
                    this.save();
                    this.render_template_selector();
                }
            );
        });

        this.wrapper.find('[data-side]').on('click', (e) => {
            e.preventDefault();
            this.current_side = $(e.target).data('side');
            this.render();
        });

        this.wrapper.find('[data-action="add_text"]').on('click', () => {
            this.add_element({
                type: 'text', content: 'New Text', x: 20, y: 50,
                style: { fontSize: '12px', fontWeight: 'normal', color: '#000000', fontFamily: 'Arial', opacity: 1 }
            });
        });

        this.wrapper.find('[data-action="add_image"]').on('click', () => {
            this.add_element({
                type: 'image', content: 'https://placehold.co/100x100', x: 20, y: 50, width: 50, height: 50, style: { opacity: 1 }
            });
        });

        this.wrapper.find('[data-action="add_watermark"]').on('click', () => {
            let w = this.data.orientation === 'horizontal' ? 337 : 212.5;
            let h = this.data.orientation === 'horizontal' ? 212.5 : 337;
            let img = this.frm.doc.watermark_image || 'https://placehold.co/200x200?text=Watermark';
            this.add_element({
                type: 'image', content: img,
                x: (w - 150) / 2, y: (h - 150) / 2, width: 150, height: 150,
                style: { opacity: 0.2 }
            }, true); // Send to back
        });

        this.wrapper.find('[data-action="add_shape"]').on('click', (e) => {
            let shape = $(e.target).data('shape');
            let w = this.data.orientation === 'horizontal' ? 337 : 212.5;
            let h = this.data.orientation === 'horizontal' ? 212.5 : 337;
            let el = { type: 'rect', style: { backgroundColor: '#3498db', opacity: 1 } };

            if (shape === 'header') {
                el.x = 0; el.y = 0; el.width = w; el.height = 40;
            } else if (shape === 'footer') {
                el.x = 0; el.y = h - 40; el.width = w; el.height = 40;
            } else {
                el.x = 20; el.y = 20; el.width = 100; el.height = 50;
            }
            this.add_element(el);
        });

        this.wrapper.find('[data-action="add_field"]').on('click', (e) => {
            let field = $(e.currentTarget).data('field');
            let el = { x: 20, y: 50, style: { opacity: 1 } };
            if (['photo', 'institute_logo', 'authority_signature', 'qr_code_image'].includes(field)) {
                el.type = 'image';
                el.mapping = field;
                el.width = 60; el.height = 60;
                if (field === 'photo') el.content = '/assets/frappe/images/default-avatar.png';
                else if (field === 'qr_code_image') el.content = 'https://placehold.co/60x60?text=QR';
                else el.content = 'https://placehold.co/60x60?text=IMG';
            } else {
                el.type = 'text';
                el.mapping = field;
                el.content = `[${$(e.currentTarget).text()}]`;
                el.style.fontSize = '12px'; el.style.fontWeight = 'bold'; el.style.color = '#000000';
            }
            this.add_element(el);
        });

        this.wrapper.find('#toggle-guides').on('change', (e) => {
            this.show_guides = $(e.target).is(':checked');
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

        if (el.type === 'text') {
            el_dom = $(`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; white-space: nowrap;">${el.content}</div>`);
            if (el.style) el_dom.css(el.style);
        } else if (el.type === 'image') {
            el_dom = $(`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; width: ${el.width}px; height: ${el.height}px; opacity: ${opacity}; overflow: hidden;">
                <img src="${el.content}" style="width: 100%; height: 100%; object-fit: cover; pointer-events: none;">
            </div>`);
            if (el.style) el_dom.css(el.style);
        } else if (el.type === 'rect') {
            el_dom = $(`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; width: ${el.width}px; height: ${el.height}px;"></div>`);
            if (el.style) el_dom.css(el.style);
        }

        el_dom.on('mousedown', (e) => {
            e.preventDefault(); e.stopPropagation();
            this.select_element(index, el_dom);
            let startX = e.clientX, startY = e.clientY;
            let elemLeft = el.x, elemTop = el.y;

            let moveHandler = (moveEvent) => {
                let dx = (moveEvent.clientX - startX) / this.scale;
                let dy = (moveEvent.clientY - startY) / this.scale;
                el.x = elemLeft + dx; el.y = elemTop + dy;
                el_dom.css({ left: el.x + 'px', top: el.y + 'px' });
            };
            let upHandler = () => {
                $(document).off('mousemove', moveHandler);
                $(document).off('mouseup', upHandler);
                this.save();
                this.show_properties(index);
            };
            $(document).on('mousemove', moveHandler);
            $(document).on('mouseup', upHandler);
        });
        this.canvas.append(el_dom);
    }

    select_element(index, dom) {
        this.canvas.find('.canvas-element').removeClass('selected');
        dom.addClass('selected');
        this.show_properties(index);
    }

    show_properties(index) {
        if (index === -1 || !this.data[this.current_side][index]) {
            // Global Properties
            this.properties.html(`
               <div class="form-group">
                    <label class="prop-label">CANVAS BACKGROUND</label>
                    <input type="color" class="form-control input-sm global-bg-change" value="${this.data.bg_color[this.current_side] || '#ffffff'}">
               </div>
               <p class="text-muted text-center" style="margin-top: 20px;">Select an element to edit.</p>
             `);
            this.wrapper.find('.global-bg-change').on('change', (e) => {
                this.data.bg_color[this.current_side] = $(e.target).val();
                this.save(); this.render();
            });
            return;
        }

        let el = this.data[this.current_side][index];
        let opacity = el.style && el.style.opacity !== undefined ? el.style.opacity : 1;

        let html = `
            <div class="row">
                <div class="col-xs-6">
                     <label class="prop-label">X POS</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="x" value="${Math.round(el.x)}">
                </div>
                <div class="col-xs-6">
                     <label class="prop-label">Y POS</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="y" value="${Math.round(el.y)}">
                </div>
            </div>
        `;

        if (el.type === 'rect' || el.type === 'image') {
            html += `
            <div class="row" style="margin-top: 5px;">
                <div class="col-xs-6">
                     <label class="prop-label">WIDTH</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="width" value="${Math.round(el.width)}">
                </div>
                <div class="col-xs-6">
                     <label class="prop-label">HEIGHT</label>
                     <input type="number" class="form-control input-sm prop-change" data-prop="height" value="${Math.round(el.height)}">
                </div>
            </div>`;

            if (el.type === 'image') {
                html += `
                <div style="margin-top: 10px;">
                    <label class="prop-label">SHAPE</label>
                    <select class="form-control input-sm shape-change">
                        <option value="rect" ${!el.shape || el.shape === 'rect' ? 'selected' : ''}>Rectangle</option>
                        <option value="circle" ${el.shape === 'circle' ? 'selected' : ''}>Circle</option>
                        <option value="triangle" ${el.shape === 'triangle' ? 'selected' : ''}>Triangle</option>
                    </select>
                </div>`;
            }

            // Border Controls for Rect and Image
            let bs = el.border_settings || { style: 'none', width: 1, color: '#000000', top: false, bottom: false, left: false, right: false };
            html += `
            <div style="margin-top: 10px; background: #f9f9f9; padding: 5px; border: 1px solid #ddd;">
                <label class="prop-label">BORDER</label>
                <div class="row">
                    <div class="col-xs-6">
                        <label class="prop-label" style="font-weight:normal">Style</label>
                        <select class="form-control input-sm border-change" data-key="style">
                            <option value="none" ${bs.style === 'none' ? 'selected' : ''}>None</option>
                            <option value="solid" ${bs.style === 'solid' ? 'selected' : ''}>Solid</option>
                            <option value="double" ${bs.style === 'double' ? 'selected' : ''}>Double</option>
                            <option value="dashed" ${bs.style === 'dashed' ? 'selected' : ''}>Dashed</option>
                        </select>
                    </div>
                    <div class="col-xs-6">
                        <label class="prop-label" style="font-weight:normal">Width (px)</label>
                        <input type="number" class="form-control input-sm border-change" data-key="width" value="${bs.width}">
                    </div>
                </div>
                <div class="row" style="margin-top: 5px;">
                    <div class="col-xs-12">
                        <label class="prop-label" style="font-weight:normal">Color</label>
                        <input type="color" class="form-control input-sm border-change" data-key="color" value="${bs.color}">
                    </div>
                </div>
                <div class="row" style="margin-top: 5px;">
                    <div class="col-xs-12">
                        <label class="prop-label" style="font-weight:normal">Sides</label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                            <input type="checkbox" class="border-change" data-key="top" ${bs.top ? 'checked' : ''}> Top
                        </label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                             <input type="checkbox" class="border-change" data-key="bottom" ${bs.bottom ? 'checked' : ''}> Bot
                        </label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                             <input type="checkbox" class="border-change" data-key="left" ${bs.left ? 'checked' : ''}> Left
                        </label>
                        <label class="checkbox-inline" style="font-size: 11px;">
                             <input type="checkbox" class="border-change" data-key="right" ${bs.right ? 'checked' : ''}> Right
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

        if (el.type === 'text') {
            html += `<hr style="margin: 10px 0;">
                <label class="prop-label">TEXT CONTENT</label>
                <input type="text" class="form-control input-sm prop-change" data-prop="content" value="${el.content}" ${el.mapping ? 'readonly' : ''}>
                <div class="row" style="margin-top:5px;">
                    <div class="col-xs-6">
                        <label class="prop-label">SIZE</label>
                        <input type="text" class="form-control input-sm style-change" data-style="fontSize" value="${el.style.fontSize}">
                    </div>
                    <div class="col-xs-6">
                        <label class="prop-label">COLOR</label>
                        <input type="color" class="form-control input-sm style-change" data-style="color" value="${el.style.color}">
                    </div>
                </div>`;
        } else if (el.type === 'rect') {
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

        this.properties.find('.prop-change').on('change', (e) => {
            let prop = $(e.target).data('prop');
            let val = $(e.target).val();
            if (['x', 'y', 'width', 'height'].includes(prop)) val = parseFloat(val);
            el[prop] = val;
            this.load_elements();
            this.canvas.find(`[data-index="${index}"]`).addClass('selected');
            this.save();
        });

        this.properties.find('.style-change').on('input change', (e) => {
            let style = $(e.target).data('style');
            let val = $(e.target).val();
            if (!el.style) el.style = {};
            el.style[style] = val;
            this.load_elements();
            this.canvas.find(`[data-index="${index}"]`).addClass('selected');
            this.save();
            // Live update opacity label
            if (style === 'opacity') $(e.target).prev().text(`OPACITY (${val})`);
        });

        this.properties.find('.tool-action').on('click', (e) => {
            let tool = $(e.currentTarget).data('tool');
            let w_canvas = this.data.orientation === 'horizontal' ? 337 : 212.5;
            let h_canvas = this.data.orientation === 'horizontal' ? 212.5 : 337;

            if (tool === 'center_h') {
                el.x = (w_canvas - (el.width || $(this.canvas.find(`[data-index="${index}"]`)).width())) / 2;
            } else if (tool === 'center_v') {
                el.y = (h_canvas - (el.height || $(this.canvas.find(`[data-index="${index}"]`)).height())) / 2;
            } else if (tool === 'bring_front') {
                this.data[this.current_side].splice(index, 1);
                this.data[this.current_side].push(el);
                this.save(); this.load_elements(); return; // Index changed
            } else if (tool === 'send_back') {
                this.data[this.current_side].splice(index, 1);
                this.data[this.current_side].unshift(el);
                this.save(); this.load_elements(); return; // Index changed
            }
            this.load_elements();
            this.canvas.find(`[data-index="${index}"]`).addClass('selected');
            this.save();
        });

        this.properties.find('.remove-el').on('click', () => {
            this.data[this.current_side].splice(index, 1);
            this.show_properties(-1);
            this.load_elements();
            this.save();
        });

        // Shape Handler
        this.properties.find('.shape-change').on('change', (e) => {
            let shape = $(e.target).val();
            el.shape = shape;
            if (!el.style) el.style = {};

            if (shape === 'circle') {
                el.style.borderRadius = '50%';
                el.style.clipPath = 'none';
            } else if (shape === 'triangle') {
                el.style.borderRadius = '0';
                el.style.clipPath = 'polygon(50% 0%, 0% 100%, 100% 100%)';
            } else {
                el.style.borderRadius = '0';
                el.style.clipPath = 'none';
            }
            this.load_elements();
            this.canvas.find(`[data-index="${index}"]`).addClass('selected');
            this.save();
        });

        // Border Handler
        this.properties.find('.border-change').on('change input', (e) => {
            let key = $(e.target).data('key');
            let val;
            if ($(e.target).attr('type') === 'checkbox') {
                val = $(e.target).is(':checked');
            } else {
                val = $(e.target).val();
            }

            if (!el.border_settings) el.border_settings = { style: 'none', width: 1, color: '#000000', top: false, bottom: false, left: false, right: false };
            el.border_settings[key] = val;

            if (!el.style) el.style = {};

            // Helper to apply per-side props
            const sides = ['top', 'bottom', 'left', 'right'];
            const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

            sides.forEach(side => {
                if (el.border_settings[side] && el.border_settings.style !== 'none') {
                    el.style[`border${cap(side)}Style`] = el.border_settings.style;
                    el.style[`border${cap(side)}Width`] = el.border_settings.width + 'px';
                    el.style[`border${cap(side)}Color`] = el.border_settings.color;
                } else {
                    el.style[`border${cap(side)}Style`] = 'none';
                    el.style[`border${cap(side)}Width`] = '0px';
                }
            });

            this.load_elements();
            this.canvas.find(`[data-index="${index}"]`).addClass('selected');
            this.save();
        });
    }

    save() {
        this.frm.set_value('canvas_data', JSON.stringify(this.data));
    }
}
