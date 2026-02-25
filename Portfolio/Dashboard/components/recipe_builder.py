from dash import html, dcc
import dash_bootstrap_components as dbc

def create_input_field(label, field_id, def_val=None, field_type="text", options=None, readonly=False):
    """Helper to create premium style inputs"""
    # Normalize ID
    cid = f"rb-{field_id.replace(' ', '_').replace('(', '').replace(')', '')}"
    
    input_comp = None
    
    if field_type == "bool":
        input_comp = dbc.Switch(
            id=cid, 
            label=label, 
            value=def_val if def_val is not None else False,
            className="ms-2 custom-switch"
        )
        return dbc.Col(input_comp, width=12, className="mb-2")
        
    elif field_type == "select":
        input_comp = dcc.Dropdown(
            id=cid,
            options=[{'label': o, 'value': o} for o in (options or [])],
            value=def_val or (options[0] if options else None),
            className="dash-dropdown",
            clearable=False,
            disabled=readonly
        )
    else: # Text/Number
        input_comp = dbc.Input(
            id=cid,
            type=field_type,
            value=def_val,
            step="any" if field_type == "number" else None,
            className="bg-dark text-white border-secondary small",
            disabled=readonly
        )
        
    return dbc.Row([
        dbc.Label(label, width=4, className="text-end small text-secondary pt-2 pe-2", style={"fontSize": "0.85rem"}),
        dbc.Col(input_comp, width=8)
    ], className="mb-2 align-items-center")


def create_recipe_builder_modal():
    return dbc.Modal([
        dbc.ModalHeader(
            html.Div([
                html.I(className="bi bi-sliders me-2 text-info"),
                "New Experiment Builder"
            ], className="h5 m-0 text-white"),
            close_button=True,
            className="border-bottom border-secondary bg-dark"
        ),
        dbc.ModalBody([
            # --- TOP SECTION: Basic, Connection, Config ---
            dbc.Row([
                # Left Column
                dbc.Col([
                    html.H6("Basic Information", className="text-info border-bottom border-secondary pb-1 mb-3 small fw-bold"),
                    create_input_field("Experiment", "Experiment", "Enabled", "select", ["Enabled", "Disabled"]),
                    create_input_field("Test Name", "Test_Name", "New_Test"),
                    create_input_field("Test Mode", "Test_Mode", "Mesh", "select", ["Mesh", "Slice"]),
                    create_input_field("Test Type", "Test_Type", "Loops", "select", ["Loops", "Sweep","Shmoo"]),
                    create_input_field("Visual ID", "Visual_ID", "", "text", readonly=True),
                    create_input_field("Bucket", "Bucket", "", "text", readonly=True),

                    html.H6("Connection", className="text-info border-bottom border-secondary pb-1 mb-3 mt-4 small fw-bold"),
                    create_input_field("COM Port", "COM_Port", 16),
                    create_input_field("IP Address", "IP_Address", "10.250.0.2"),
                    create_input_field("TTL Folder", "TTL_Folder", "C:/SystemDebug/TTL_Linux/"),
                    create_input_field("Scripts File", "Scripts_File", ""),
                    create_input_field("Post Process", "Post_Process", ""),
                    
                    # Validation Message Area
                    html.Div(id="rb-validation-msg", className="small mt-3 text-warning", style={"minHeight": "20px"})
                ], md=6),
                
                # Right Column
                dbc.Col([
                    dbc.Row([
                        dbc.Col(html.H6("Test Configuration", className="text-info border-bottom border-secondary pb-1 mb-3 small fw-bold"), width=10),
                        dbc.Col(dbc.Button(html.I(className="bi bi-plus-circle"), id="btn-open-script-modal", size="sm", color="link", className="text-info p-0"), width=2, className="text-end")
                    ]),
                    create_input_field("Content", "Content", "Linux", "select", ["Linux", "Dragon"]),
                    create_input_field("Script Template", "Script", "Baseline", "select", ["Baseline", "Stress", "Functional", "Custom"]),
                    
                    # Custom Script Fields (Hidden by default)
                    html.Div([
                         create_input_field("Custom Name", "Custom_Script_Name", ""),
                         create_input_field("Script Path", "Custom_Script_Path", ""),
                    ], id="section-custom-script", style={"display": "none"}, className="ps-3 border-start border-info mb-2"),
                    
                    create_input_field("Pass String", "Pass_String", "Test Complete"),
                    create_input_field("Fail String", "Fail_String", "Test Failed"),
                    create_input_field("Test Number", "Test_Number", 1, "number"),
                    create_input_field("Test Time (s)", "Test_Time", 30, "number"),

                    html.Div("Flags & Config", className="text-secondary small mt-3 mb-2 fw-bold"),
                    dbc.Row([
                        dbc.Col([
                            create_input_field("Reset", "Reset", True, "bool"),
                            create_input_field("FastBoot", "FastBoot", True, "bool"),
                            create_input_field("Reset on PASS", "Reset_on_PASS", True, "bool"),
                            create_input_field("Core License", "Core_License", ""),
                        ], width=6),
                        dbc.Col([
                            create_input_field("600W Unit", "600W_Unit", False, "bool"),
                            create_input_field("Pseudo Cfg", "Pseudo_Config", False, "bool"),
                            create_input_field("Dis 2 Cores", "Disable_2_Cores", False, "bool"),
                        ], width=6)
                    ]),
                    create_input_field("Config Mask", "Configuration_Mask", ""),
                    create_input_field("Boot Breakpoint", "Boot_Breakpoint", ""),
                    create_input_field("Check Core", "Check_Core", ""),
                ], md=6),
            ]),
            
            # --- DYNAMIC SECTIONS ---
            
            # Voltage / Frequency (Loops)
            html.Div(id="section-voltage", style={"display": "block"}, children=[
                html.H6("Voltage / Frequency (Loops)", className="text-warning border-bottom border-secondary pb-1 mb-3 mt-4 small fw-bold"),
                dbc.Row([
                    dbc.Col([
                        create_input_field("Voltage Type", "Voltage_Type", "vbump", "select", ["vbump", "fixed"]),
                        create_input_field("Voltage IA", "Voltage_IA", "", "number"),
                        create_input_field("Voltage CFC", "Voltage_CFC", "", "number"),
                    ], md=6),
                    dbc.Col([
                        create_input_field("Loops", "Loops", 1, "number"),
                        create_input_field("Frequency IA", "Frequency_IA", "", "number"),
                        create_input_field("Frequency CFC", "Frequency_CFC", "", "number"),
                    ], md=6),
                ])
            ]),
            
            # Sweep Parameters
            html.Div(id="section-sweep", style={"display": "none"}, children=[
                 html.H6("Sweep Parameters", className="text-warning border-bottom border-secondary pb-1 mb-3 mt-4 small fw-bold"),
                 dbc.Row([
                    dbc.Col([
                        create_input_field("Type", "Sweep_Type", "Voltage", "select", ["Voltage", "Frequency"]),
                        create_input_field("Domain", "Sweep_Domain", "IA", "select", ["IA", "CFC"]),
                        create_input_field("Shmoo File", "ShmooFile", "C:\\SystemDebug\\Shmoos\\RVPShmooConfig.json"),
                    ], md=6),
                    dbc.Col([
                        create_input_field("Start", "Start", -0.05, "number"),
                        create_input_field("End", "End", 0.05, "number"),
                        create_input_field("Steps", "Steps", 0.01, "number"),
                        create_input_field("Label", "ShmooLabel", "COREFIX"),
                    ], md=6),
                 ])
            ]),

            # Linux Config
            html.Div(id="section-linux", style={"display": "block"}, children=[
                 html.H6("Linux Configuration", className="text-success border-bottom border-secondary pb-1 mb-3 mt-4 small fw-bold"),
                 dbc.Row([
                    dbc.Col([
                        create_input_field("Startup Linux", "Startup_Linux", "startup_linux.nsh"),
                        create_input_field("Linux Pre Cmd", "Linux_Pre_Command", ""),
                        create_input_field("Linux Pass", "Linux_Pass_String", ""),
                        create_input_field("Wait Time", "Linux_Content_Wait_Time", ""),
                        create_input_field("Content Line 0", "Linux_Content_Line_0", ""),
                        create_input_field("Content Line 1", "Linux_Content_Line_1", ""),
                    ], md=6),
                    dbc.Col([
                        create_input_field("Linux Path", "Linux_Path", ""),
                        create_input_field("Linux Post Cmd", "Linux_Post_Command", ""),
                        create_input_field("Linux Fail", "Linux_Fail_String", ""),
                        create_input_field("Content Line 2", "Linux_Content_Line_2", ""),
                        create_input_field("Content Line 3", "Linux_Content_Line_3", ""),
                        create_input_field("Content Line 4", "Linux_Content_Line_4", ""),
                        create_input_field("Content Line 5", "Linux_Content_Line_5", ""),
                    ], md=6),
                 ])
            ]),

            # Dragon Config
            html.Div(id="section-dragon", style={"display": "none"}, children=[
                 html.H6("Dragon Configuration", className="text-danger border-bottom border-secondary pb-1 mb-3 mt-4 small fw-bold"),
                 dbc.Row([
                    dbc.Col([
                        create_input_field("Startup Dragon", "Startup_Dragon", "startup_efi.nsh"),
                        create_input_field("ULX Path", "ULX_Path", "FS1:\\EFI\\ulx"),
                        create_input_field("VVAR0", "VVAR0", "0x4C4B40"),
                        create_input_field("VVAR2", "VVAR2", "0x1000000"),
                        create_input_field("VVAR Extra", "VVAR_EXTRA", ""),
                        create_input_field("Dragon Pre", "Dragon_Pre_Command", ""),
                        create_input_field("Merlin Name", "Merlin_Name", "MerlinX.efi"),
                        create_input_field("Merlin Drive", "Merlin_Drive", "FS1:"),
                    ], md=6),
                    dbc.Col([
                        create_input_field("Content Path", "Dragon_Content_Path", "FS1:\\content\\Dragon\\"),
                        create_input_field("Content Line", "Dragon_Content_Line", ""),
                        create_input_field("Merlin Path", "Merlin_Path", "FS1:\\EFI\\Version8.15\\"),
                        create_input_field("VVAR1", "VVAR1", 80064000),
                        create_input_field("VVAR3", "VVAR3", "0x4000000"),
                        create_input_field("Dragon Post", "Dragon_Post_Command", ""),
                        create_input_field("Stop on Fail", "Stop_on_Fail", True, "bool"),
                    ], md=6),
                 ])
            ]),

        ], className="bg-dark text-white", style={"maxHeight": "75vh", "overflowY": "auto"}), # Scrollable body
        
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-cancel-recipe", className="me-auto btn-outline-custom"),
            dbc.Button([html.I(className="bi bi-check-lg me-2"), "Create Experiment"], id="btn-create-recipe", className="btn-primary-custom")
        ], className="border-top border-secondary bg-dark")
    ], id="modal-recipe-builder", size="xl", backdrop="static")

def create_script_manager_modal():
    return dbc.Modal([
        dbc.ModalHeader(html.H5("Add New Script Condition", className="text-info m-0"), close_button=True, className="bg-dark border-secondary"),
        dbc.ModalBody([
            dbc.Label("Condition Name (e.g. Dis_PowerDowns)", className="small text-secondary"),
            dbc.Input(id="new-script-name", className="bg-dark text-white border-secondary mb-3"),
            dbc.Label("Script Path", className="small text-secondary"),
            dbc.Input(id="new-script-path", className="bg-dark text-white border-secondary mb-3"),
            html.Div(id="script-modal-msg", className="small text-warning")
        ], className="bg-dark text-white"),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-cancel-script", size="sm", outline=True, color="secondary"),
            dbc.Button("Save Condition", id="btn-save-script", size="sm", color="info")
        ], className="bg-dark border-secondary")
    ], id="modal-script-manager", size="md")
