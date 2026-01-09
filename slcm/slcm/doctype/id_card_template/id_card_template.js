
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

        let raw_data = frm.doc.canvas_data;
        if (!raw_data) {
            this.data = { front: [], back: [], orientation: 'horizontal', bg_color: { front: '#ffffff', back: '#ffffff' } };
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
                this.data = { front: [], back: [], orientation: 'horizontal', bg_color: { front: '#ffffff', back: '#ffffff' } };
            }
        }

        this.current_side = 'front';
        this.scale = 1.5;
        this.render();
    }

    render() {
        let width, height;
        if (this.data.orientation === 'horizontal') {
            width = 337;
            height = 212;
        } else {
            width = 212;
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
                            
                            <hr style="margin: 10px 0;">
                            <label class="prop-label">FIELDS</label>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="student_name">Student Name</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="photo">Student Photo</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="student_id">Student ID</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="blood_group">Blood Group</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="qr_code_image">QR Code</button>
                            
                            <hr style="margin: 10px 0;">
                            <label class="prop-label">INSTITUTE</label>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="institute_logo">Institute Logo</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="authority_signature">Authority Signature</button>
                            <button class="btn btn-default btn-block btn-xs tool-btn" data-action="add_field" data-field="institute_name">Institute Name</button>
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
                        border-radius: 4px;
                        min-height: 400px;
                        align-items: center;
                    ">
                        <div id="card-canvas" style="
                            width: ${width}px; 
                            height: ${height}px; 
                            background: ${this.data.bg_color[this.current_side] || '#ffffff'};
                            position: relative;
                            overflow: hidden;
                            transform: scale(${this.scale}); 
                            transform-origin: center center;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        ">
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
            let w = this.data.orientation === 'horizontal' ? 337 : 212;
            let h = this.data.orientation === 'horizontal' ? 212 : 337;
            let img = this.frm.doc.watermark_image || 'https://placehold.co/200x200?text=Watermark';
            this.add_element({
                type: 'image', content: img,
                x: (w - 150) / 2, y: (h - 150) / 2, width: 150, height: 150,
                style: { opacity: 0.2 }
            }, true); // Send to back
        });

        this.wrapper.find('[data-action="add_shape"]').on('click', (e) => {
            let shape = $(e.target).data('shape');
            let w = this.data.orientation === 'horizontal' ? 337 : 212;
            let h = this.data.orientation === 'horizontal' ? 212 : 337;
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
            el_dom = $(`<div class="canvas-element" data-index="${index}" style="position: absolute; left: ${el.x}px; top: ${el.y}px; width: ${el.width}px; height: ${el.height}px; opacity: ${opacity};">
                <img src="${el.content}" style="width: 100%; height: 100%; object-fit: cover; pointer-events: none;">
            </div>`);
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
            let w_canvas = this.data.orientation === 'horizontal' ? 337 : 212;
            let h_canvas = this.data.orientation === 'horizontal' ? 212 : 337;

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
    }

    save() {
        this.frm.set_value('canvas_data', JSON.stringify(this.data));
    }
}
