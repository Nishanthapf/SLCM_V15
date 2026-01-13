/* global slcm */
frappe.provide("slcm.templates");

slcm.templates.field_map = {
	student_name: { source: "student_name", type: "text", required: true },
	student_id: { source: "name", type: "text", required: true },
	program: { source: "program", type: "text", required: true },
	department: { source: "department", type: "text", required: true },
	email: { source: "email", type: "text", required: false },
	phone: { source: "phone", type: "text", required: false },
	date_of_birth: { source: "date_of_birth", type: "date", required: false },
	blood_group: { source: "blood_group", type: "text", required: false }, // Fetched from Student Master map
	issue_date: { source: "issue_date", type: "date", required: true },
	expiry_date: { source: "expiry_date", type: "date", required: true },
	// Images
	photo: { source: "photo", type: "image", required: true },
	qr_code_image: { source: "qr_code_image", type: "image", required: true },
	institute_logo: { source: "institute_logo", type: "image", required: true }, // From Template
	authority_signature: { source: "authority_signature", type: "image", required: false }, // From Template
};

slcm.templates.registry = [
	{
		template_id: "nlsiu_style",
		template_name: "NLSIU Style",
		orientation: "Horizontal",
		card_size: "CR80",
		front_template_html: `
<div style="width: 1011px; height: 638px; background-color: white; color: black; font-family: 'Times New Roman', serif; position: relative; border: 1px solid #ccc; box-sizing: border-box; overflow: hidden;">
    <!-- Main Content Area (Left side) -->
    <div style="position: absolute; top: 0; left: 0; right: 128px; height: 100%; padding: 40px; display: flex; align-items: center;">

        <!-- Photo -->
        <div style="width: 180px; height: 220px; border: 1px solid black; flex-shrink: 0; margin-right: 40px;">
            <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>

        <!-- Details -->
        <div style="font-family: Arial, sans-serif; font-size: 24px; line-height: 2; flex-grow: 1;">
            <div style="display: flex;">
                <div style="width: 200px; font-weight: bold;">NAME</div>
                <div style="margin-right: 15px;">:</div>
                <div style="font-weight: bold; text-transform: uppercase;">{{ student_name }}</div>
            </div>
            <div style="display: flex;">
                <div style="width: 200px; font-weight: bold;">ID No</div>
                <div style="margin-right: 15px;">:</div>
                <div style="font-weight: bold;">{{ name }}</div>
            </div>
             <div style="display: flex;">
                <div style="width: 200px; font-weight: bold;">COURSE</div>
                <div style="margin-right: 15px;">:</div>
                <div style="font-weight: bold; text-transform: uppercase;">{{ program }}</div>
            </div>
             <div style="display: flex;">
                <div style="width: 200px; font-weight: bold;">BLOOD GROUP</div>
                <div style="margin-right: 15px;">:</div>
                 <div style="font-weight: bold;">{{ blood_group }}</div>
            </div>
        </div>
    </div>

    <!-- Signature (Bottom Left) -->
    <div style="position: absolute; bottom: 40px; left: 60px;">
            <img src="{{ authority_signature }}" style="height: 60px; display: block; margin-bottom: 5px;">
            <div style="font-family: Arial, sans-serif; font-weight: bold; font-size: 20px;">Registrar</div>
    </div>

    <!-- Vertical Header Strip (Right Edge) -->
    <div style="position: absolute; top: 0; right: 0; width: 128px; height: 100%; border-left: 1px solid #000; display: flex; flex-direction: column; align-items: center; padding-top: 30px;">
        <!-- Logo -->
        <img src="{{ institute_logo }}" style="width: 90px; height: auto; margin-bottom: 20px;">

        <!-- Divider -->
        <div style="width: 100px; height: 1px; background-color: #000; margin-bottom: 20px;"></div>

        <!-- Rotated Text -->
        <div style="writing-mode: vertical-rl; text-orientation: mixed; font-weight: bold; font-size: 24px; letter-spacing: 0.5px; text-align: center; height: 480px; font-family: 'Times New Roman', serif;">
            NATIONAL LAW SCHOOL OF INDIA UNIVERSITY
            <br>
            BENGALURU
            <span style="font-family: Arial, sans-serif; font-size: 20px; margin-top: 30px; display: inline-block;">STUDENT IDENTITY CARD</span>
        </div>
    </div>
</div>`,
		back_template_html: `
<div style="width: 1011px; height: 638px; background-color: white; color: black; font-family: Arial, sans-serif; position: relative; border: 1px solid #ccc; box-sizing: border-box; overflow: hidden;">

    <!-- Warning Box -->
    <div style="position: absolute; bottom: 40px; left: 60px; right: 160px; border: 2px solid black; padding: 15px; text-align: center;">
        <div style="font-weight: bold; font-size: 22px; text-transform: uppercase;">THIS CARD IS TO BE CARRIED BY YOU AT ALL TIMES</div>
    </div>

    <!-- Instructions Area -->
    <div style="position: absolute; top: 60px; left: 60px; right: 160px; bottom: 120px; display: flex; align-items: center;">
        <div style="font-size: 24px; line-height: 1.5;">
            <ol style="padding-left: 30px;">
                <li style="margin-bottom: 15px;">The card should be produced on demand to security staff or any other authorised person.</li>
                <li style="margin-bottom: 15px;">Loss of this card must be immediately reported to pmc@nls.ac.in or itsupport@nls.ac.in.</li>
                <li style="margin-bottom: 15px;">This card is non-transferable and must be surrendered immediately after graduation or cessation of employment/contract.</li>
                <li style="margin-bottom: 15px;">If found, please return the card to NLSIU Bangalore (Ph: 23213160/23160532/33/35)</li>
            </ol>
        </div>
    </div>

    <!-- Vertical Strip (Right) -->
    <div style="position: absolute; top: 0; right: 0; width: 100px; height: 100%; border-left: 2px solid #000; display: flex; align-items: center; justify-content: center;">
         <div style="writing-mode: vertical-rl; text-orientation: mixed; font-weight: bold; font-size: 32px; letter-spacing: 1px; font-family: 'Times New Roman', serif;">
            INSTRUCTIONS :
        </div>
    </div>
</div>`,
	},
	{
		template_id: "uni_std_vert",
		template_name: "University Standard - Vertical",
		orientation: "Vertical",
		card_size: "CR80",
		front_template_html: `
<div style="width: 638px; height: 1011px; background: white; border: 1px solid #ddd; position: relative; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; overflow: hidden;">
    <!-- Header with Logo -->
    <div style="background-color: #002147; height: 160px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
        <img src="{{ institute_logo }}" style="height: 80px; margin-bottom: 10px; filter: brightness(0) invert(1);">
        <div style="color: white; font-size: 28px; font-weight: bold; text-transform: uppercase;">{{ institute_name }}</div>
    </div>

    <!-- Photo Section -->
    <div style="text-align: center; margin-top: 60px;">
        <div style="width: 300px; height: 300px; border-radius: 50%; overflow: hidden; border: 8px solid #f0f0f0; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
    </div>

    <!-- Student Details -->
    <div style="text-align: center; margin-top: 40px; padding: 0 40px;">
        <h1 style="margin: 0; color: #333; font-size: 42px; font-weight: 700; text-transform: uppercase;">{{ student_name }}</h1>
        <p style="margin: 10px 0 0 0; color: #666; font-size: 24px;">{{ program }}</p>
        <div style="margin-top: 30px; font-size: 22px; color: #444; line-height: 1.6;">
            <strong>ID:</strong> {{ name }}<br>
            <strong>Dept:</strong> {{ department }}<br>
            <strong>DOB:</strong> {{ date_of_birth }}
        </div>
    </div>

    <!-- Footer -->
    <div style="position: absolute; bottom: 40px; width: 100%; text-align: center;">
        <div style="font-size: 18px; color: #002147; font-weight: bold;">STUDENT ID CARD</div>
    </div>
</div>`,
		back_template_html: `
<div style="width: 638px; height: 1011px; background: #f9f9f9; position: relative; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; overflow: hidden;">
    <div style="padding: 60px;">
        <!-- Terms -->
        <h3 style="color: #002147; font-size: 28px; border-bottom: 2px solid #002147; padding-bottom: 10px;">Terms & Conditions</h3>
        <ul style="font-size: 20px; color: #444; line-height: 1.6; padding-left: 24px;">
            <li>This card is the property of {{ institute_name }}.</li>
            <li>If found, please return to the Registrar's Office.</li>
            <li>Valid only for current academic session.</li>
            <li>Non-transferable.</li>
        </ul>

        <!-- Details -->
        <div style="margin-top: 60px; font-size: 22px; color: #333;">
            <p><strong>Emergency Contact:</strong> {{ phone }}</p>
            <p><strong>Blood Group:</strong> {{ blood_group }}</p>
            <p><strong>Valid Until:</strong> {{ expiry_date }}</p>
        </div>

        <!-- Signature & QR -->
        <div style="position: absolute; bottom: 60px; left: 0; width: 100%; padding: 0 60px; box-sizing: border-box; display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="text-align: center;">
                <img src="{{ authority_signature }}" style="height: 80px; display: block; margin-bottom: 5px;">
                <div style="border-top: 1px solid #333; width: 200px; padding-top: 5px; font-size: 18px;">Registrar Signature</div>
            </div>
            <div>
                <img src="{{ qr_code_image }}" style="width: 180px; height: 180px; border: 4px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            </div>
        </div>
    </div>
</div>`,
	},
	{
		template_id: "uni_std_horiz",
		template_name: "University Standard - Horizontal",
		orientation: "Horizontal",
		card_size: "CR80",
		front_template_html: `
<div style="width: 1011px; height: 638px; background: white; position: relative; font-family: Arial, sans-serif; display: flex; overflow: hidden;">
    <!-- Left Sidebar -->
    <div style="width: 350px; background-color: #002147; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
        <div style="width: 220px; height: 220px; border-radius: 12px; overflow: hidden; border: 4px solid white;">
            <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
        <div style="margin-top: 30px; text-align: center; color: white;">
            <div style="font-size: 20px; font-weight: bold; opacity: 0.8;">STUDENT</div>
            <div style="font-size: 32px; font-weight: bold; margin-top: 5px;">{{ name }}</div>
        </div>
    </div>

    <!-- Right Content -->
    <div style="flex: 1; padding: 40px; position: relative;">
        <div style="display: flex; align-items: center; margin-bottom: 40px;">
            <img src="{{ institute_logo }}" style="height: 60px; margin-right: 20px;">
            <div style="font-size: 28px; font-weight: bold; color: #002147;">{{ institute_name }}</div>
        </div>

        <div style="margin-top: 20px;">
            <h1 style="margin: 0; font-size: 40px; font-weight: 700; color: #333;">{{ student_name }}</h1>
            <p style="margin: 10px 0 0 0; font-size: 24px; color: #666;">{{ program }} | {{ department }}</p>

            <div style="margin-top: 40px; font-size: 20px; color: #444;">
                Valid To: <strong>{{ expiry_date }}</strong>
            </div>
        </div>

        <div style="position: absolute; bottom: 30px; right: 40px;">
            <img src="{{ institute_logo }}" style="height: 40px; opacity: 0.1;">
        </div>
    </div>
</div>`,
		back_template_html: `
<div style="width: 1011px; height: 638px; background: #fff; position: relative; font-family: Arial, sans-serif; border-left: 20px solid #cecece;">
    <div style="padding: 50px; display: flex; height: 100%; box-sizing: border-box;">
        <div style="flex: 1;">
            <h3 style="margin-top: 0; color: #333; font-size: 24px; text-transform: uppercase;">Instructions</h3>
            <p style="font-size: 18px; color: #555; line-height: 1.5;">
                This card must be carried at all times while on campus.
                Loss of card must be reported immediately.
            </p>

             <div style="margin-top: 40px;">
                <p><strong>Address:</strong> {{ institute_address }}</p>
                <p><strong>Phone:</strong> {{ phone }}</p>
            </div>

            <div style="margin-top: 60px;">
                 <img src="{{ authority_signature }}" style="height: 60px;">
                 <div style="font-size: 16px; font-weight: bold;">Registrar</div>
            </div>
        </div>

        <div style="width: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-left: 2px solid #eee; padding-left: 40px;">
             <img src="{{ qr_code_image }}" style="width: 250px; height: 250px;">
             <div style="margin-top: 10px; font-size: 16px; color: #888;">Scan to Verify</div>
        </div>
    </div>
</div>`,
	},
	{
		template_id: "hostel_id",
		template_name: "Hostel ID Card",
		orientation: "Vertical",
		card_size: "CR80",
		front_template_html: `
<div style="width: 638px; height: 1011px; background: #f4f7f6; position: relative; font-family: 'Verdana', sans-serif;">
    <div style="background-color: #2c3e50; height: 120px; padding: 20px; display: flex; align-items: center;">
         <img src="{{ institute_logo }}" style="height: 80px; filter: brightness(0) invert(1);">
         <div style="color: white; margin-left: 20px; font-size: 30px; font-weight: bold;">HOSTEL RESIDENT</div>
    </div>

    <div style="padding: 40px; text-align: center;">
        <div style="width: 280px; height: 280px; border-radius: 10px; background: #ddd; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
             <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>

        <h2 style="margin: 30px 0 10px; font-size: 36px; color: #2c3e50;">{{ student_name }}</h2>
        <div style="font-size: 24px; color: #7f8c8d;">Room: 304 - Block B</div>

        <table style="width: 100%; margin-top: 40px; text-align: left; font-size: 20px; color: #34495e;">
            <tr><td style="padding: 10px; font-weight: bold;">Student ID:</td><td>{{ name }}</td></tr>
            <tr><td style="padding: 10px; font-weight: bold;">Blood Group:</td><td>{{ blood_group }}</td></tr>
            <tr><td style="padding: 10px; font-weight: bold;">Emergency:</td><td>{{ phone }}</td></tr>
        </table>
    </div>

     <div style="position: absolute; bottom: 0; width: 100%; height: 20px; background: #e74c3c;"></div>
</div>`,
		back_template_html: `
<div style="width: 638px; height: 1011px; background: white; text-align: center; padding: 60px; box-sizing: border-box; font-family: 'Verdana', sans-serif;">
    <img src="{{ qr_code_image }}" style="width: 300px; height: 300px;">
    <h3 style="margin-top: 40px;">GATE PASS</h3>
    <p>Use this QR Code for Hostel Entry/Exit.</p>
</div>`,
	},
	{
		template_id: "library_card",
		template_name: "Library Access Card",
		orientation: "Horizontal",
		card_size: "CR80",
		front_template_html: `
<div style="width: 1011px; height: 638px; background: #fffbe7; font-family: 'Georgia', serif; border: 8px double #5d4037; position: relative;">
    <div style="position: absolute; top: 30px; left: 30px;">
         <img src="{{ institute_logo }}" style="height: 80px;">
    </div>
    <div style="text-align: center; padding-top: 40px;">
        <h1 style="font-size: 48px; color: #5d4037; margin-bottom: 5px;">LIBRARY CARD</h1>
        <div style="font-size: 20px; font-style: italic;">{{ institute_name }}</div>
    </div>

    <div style="display: flex; margin-top: 50px; padding: 0 60px;">
        <div style="border: 2px solid #5d4037; width: 200px; height: 250px; padding: 5px;">
             <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
        <div style="flex: 1; padding-left: 40px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 36px; font-weight: bold; color: #3e2723; border-bottom: 2px solid #5d4037; display: inline-block;">{{ student_name }}</div>
            <div style="font-size: 24px; margin-top: 20px;"><strong>Member ID:</strong> {{ name }}</div>
            <div style="font-size: 24px; margin-top: 10px;"><strong>Dept:</strong> {{ department }}</div>
        </div>
    </div>
    <div style="position: absolute; bottom: 30px; right: 40px;">
         <img src="{{ qr_code_image }}" style="width: 120px; height: 120px;">
    </div>
</div>`,
		back_template_html: ``,
	},
	{
		template_id: "visitor_id",
		template_name: "Temporary / Visitor ID",
		orientation: "Vertical",
		card_size: "CR80",
		front_template_html: `
<div style="width: 638px; height: 1011px; background: #FFF; border-top: 50px solid #FF9800; font-family: sans-serif;">
    <div style="text-align: center; padding-top: 60px;">
        <h1 style="font-size: 60px; color: #F57C00; margin: 0;">VISITOR</h1>
        <p style="font-size: 24px; color: #666;">Temporary Pass</p>
    </div>
    <div style="margin: 60px 40px; border: 2px dashed #ccc; padding: 40px; text-align: center;">
        <div style="font-size: 30px; font-weight: bold; margin-bottom: 20px;">{{ student_name }}</div>
        <div style="font-size: 20px; color: #888;">Valid for 1 Day</div>
    </div>
    <div style="text-align: center;">
         <img src="{{ qr_code_image }}" style="width: 250px;">
    </div>
</div>`,
		back_template_html: ``,
	},
	{
		template_id: "test_visitor_id",
		template_name: "Test Visitor ID",
		orientation: "Vertical",
		card_size: "CR80",
		front_template_html: `
<div style="width: 638px; height: 1011px; background: #e0f7fa; border: 5px solid #006064; font-family: monospace;">
    <div style="text-align: center; padding-top: 50px;">
        <h1 style="color: #006064;">TEST VISITOR</h1>
        <p>Debugging Template</p>
    </div>
    <div style="padding: 20px; font-size: 18px;">
        <p><strong>Name:</strong> {{ student_name }}</p>
        <p><strong>ID:</strong> {{ name }}</p>
        <p><strong>Dept:</strong> {{ department }}</p>
    </div>
     <div style="text-align: center; margin-top: 50px;">
         <img src="{{ qr_code_image }}" style="width: 200px; border: 2px solid #000;">
         <p>QR Code Check</p>
    </div>
</div>`,
		back_template_html: ``,
	},
	{
		template_id: "faculty_id",
		template_name: "Faculty ID Card",
		orientation: "Vertical",
		card_size: "CR80",
		front_template_html: `
<div style="width: 638px; height: 1011px; background: white; border: 1px solid #ddd; position: relative; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; overflow: hidden;">
    <div style="background-color: #8B0000; height: 160px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
        <img src="{{ institute_logo }}" style="height: 80px; margin-bottom: 10px; filter: brightness(0) invert(1);">
        <div style="color: white; font-size: 28px; font-weight: bold; text-transform: uppercase;">{{ institute_name }}</div>
    </div>
    <div style="text-align: center; margin-top: 60px;">
        <div style="width: 300px; height: 300px; border-radius: 5px; overflow: hidden; border: 4px solid #8B0000; margin: 0 auto;">
            <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
        </div>
    </div>
    <div style="text-align: center; margin-top: 40px; padding: 0 40px;">
        <h1 style="margin: 0; color: #333; font-size: 42px; font-weight: 700; text-transform: uppercase;">{{ student_name }}</h1>
        <p style="margin: 10px 0 0 0; color: #8B0000; font-size: 28px; font-weight: bold;">FACULTY</p>
        <div style="margin-top: 30px; font-size: 22px; color: #444; line-height: 1.6;">
            <strong>ID:</strong> {{ name }}<br>
            <strong>Dept:</strong> {{ department }}
        </div>
    </div>
    <div style="position: absolute; bottom: 0; width: 100%; height: 20px; background: #8B0000;"></div>
</div>`,
		back_template_html: `
<div style="width: 638px; height: 1011px; background: #f9f9f9; position: relative; font-family: sans-serif;">
    <div style="padding: 60px;">
        <div style="text-align: center; margin-bottom: 40px;">
             <img src="{{ institute_logo }}" style="height: 60px;">
        </div>
        <p style="font-size: 20px; line-height: 1.6;">Use this card for campus access, library, and other faculty privileges.</p>
        <div style="margin-top: 60px;">
            <p><strong>Emergency:</strong> {{ phone }}</p>
            <p><strong>Blood Group:</strong> {{ blood_group }}</p>
        </div>
        <div style="position: absolute; bottom: 60px; text-align: center; width: 100%; left:0;">
             <img src="{{ qr_code_image }}" style="width: 200px; height: 200px;">
        </div>
    </div>
</div>`,
	},
	{
		template_id: "driver_id",
		template_name: "Driver ID Card",
		orientation: "Horizontal",
		card_size: "CR80",
		front_template_html: `
<div style="width: 1011px; height: 638px; background: #fff; border: 8px solid #336600; display: flex; font-family: Arial, sans-serif; position: relative;">
    <div style="width: 300px; background: #336600; display: flex; align-items: center; justify-content: center;">
        <div style="color: white; font-size: 40px; font-weight: bold; transform: rotate(-90deg); white-space: nowrap;">DRIVER</div>
    </div>
    <div style="flex: 1; padding: 40px;">
        <div style="display: flex; align-items: flex-start;">
             <img src="{{ institute_logo }}" style="height: 80px; margin-right: 20px;">
             <div>
                 <div style="font-size: 32px; font-weight: bold; color: #336600;">{{ institute_name }}</div>
                 <div style="font-size: 18px; color: #555;">Transport Department</div>
             </div>
        </div>
        <div style="display: flex; margin-top: 40px;">
             <div style="width: 200px; height: 240px; border: 2px solid #ccc; background: #eee;">
                  <img src="{{ passport_size_photo }}" style="width: 100%; height: 100%; object-fit: cover;">
             </div>
             <div style="margin-left: 40px; font-size: 24px;">
                 <div style="font-weight: bold; font-size: 36px; margin-bottom: 10px;">{{ student_name }}</div>
                 <div>ID: <strong>{{ name }}</strong></div>
                 <div style="margin-top: 10px;">{{ phone }}</div>
             </div>
        </div>
    </div>
</div>`,
		back_template_html: `
<div style="width: 1011px; height: 638px; background: #f0f0f0; padding: 50px; box-sizing: border-box; font-family: sans-serif;">
    <h2>Vehicle Operation Rules</h2>
    <ul style="font-size: 20px; line-height: 1.8;">
        <li>Carry this card while on duty.</li>
        <li>Follow all traffic rules.</li>
        <li>Report accidents immediately.</li>
    </ul>
     <div style="position: absolute; bottom: 50px; right: 50px;">
          <img src="{{ qr_code_image }}" style="width: 150px; height: 150px;">
     </div>
</div>`,
	},
];

// Helper to get template by ID
slcm.templates.get = function (id) {
	return slcm.templates.registry.find((t) => t.template_id === id);
};
