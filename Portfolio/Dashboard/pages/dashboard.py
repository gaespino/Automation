import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ctx, ClientsideFunction
import dash_bootstrap_components as dbc
import time
import json
import numpy as np

from components.unit_selector import create_unit_selector
from components.stats_card import create_stats_card, generate_stats_view
from components.experiments_grid import create_experiments_grid
from components.recipe_builder import create_recipe_builder_modal, create_script_manager_modal
from components.modals import create_recipe_viewer_modal, create_unit_creation_modal, create_product_modal, create_bucket_modal, create_save_recipe_modal, create_load_recipe_modal
from services.data_handler import DataHandler
from services.unit_service import UnitService
from services.experiment_service import ExperimentService
from services.template_service import TemplateService

# Layout
layout = dbc.Container(fluid=True, className="pb-5", children=[
    dcc.Store(id='store-unit-data'),
    dcc.Store(id='store-refresh-trigger', data=0),
    
    # Toast for notifications
    html.Div(id="dash-toast-anchor"),

    # MODALS
    create_recipe_builder_modal(),
    create_script_manager_modal(),
    create_recipe_viewer_modal(),
    create_unit_creation_modal(),
    create_product_modal(),
    create_bucket_modal(),
    create_save_recipe_modal(),
    create_load_recipe_modal(),

    dbc.Row([
        # Sidebar
        dbc.Col(md=3, lg=3, xl=2, children=[
            create_unit_selector()
        ]),
        
        # Main Content
        dbc.Col(md=9, lg=9, xl=10, children=[
            html.Div(id='stats-card-container'),
            create_experiments_grid()
        ])
    ])
])

# --- Callbacks ---

# Data Loading (1-5) - reusing standard logic
@callback(Output('sel-product', 'options'), Input('url', 'pathname'))
def load_products(_):
    prods = DataHandler.get_products()
    return [{'label': p, 'value': p} for p in prods]

@callback([Output('sel-bucket', 'options'), Output('sel-bucket', 'disabled')], Input('sel-product', 'value'))
def update_buckets(product):
    if not product: return [], True
    return [{'label': b, 'value': b} for b in DataHandler.get_buckets(product)], False

@callback([Output('sel-unit', 'options'), Output('sel-unit', 'disabled')], 
          [Input('sel-platform', 'value'), Input('sel-bucket', 'value'), State('sel-product', 'value')])
def update_units(platform, bucket, product):
    if not (platform and bucket and product): return [], True
    return [{'label': u, 'value': u} for u in DataHandler.get_units(product, bucket, platform)], False

@callback([Output('store-unit-data', 'data'), Output('btn-load-data', 'disabled')],
          [Input('sel-unit', 'value'), Input('store-refresh-trigger', 'data'), 
           State('sel-product', 'value'), State('sel-bucket', 'value'), State('sel-platform', 'value')])
def load_unit_data(unit, refresh, product, bucket, platform):
    if not unit: return None, True
    data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
    if data:
        data['_context'] = {'product': product, 'bucket': bucket, 'unit': unit, 'platform': platform}
        return data, False 
    return None, True

@callback([Output('stats-card-container', 'children'), Output('experiments-grid', 'rowData')],
          Input('store-unit-data', 'data'))
def update_dashboard_view(data):
    if not data: return html.Div(dbc.Alert("Please select a unit to view details.", color="secondary", className="card-premium border-0 text-white")), []
    return generate_stats_view(data), data.get("experiments", [])

@callback(Output('btn-save', 'disabled'), Input('experiments-grid', 'cellValueChanged'), prevent_initial_call=True)
def enable_save(change): return False

# 7. Action Button Logic
@callback(
    [Output('dash-toast-anchor', 'children', allow_duplicate=True), Output('store-refresh-trigger', 'data', allow_duplicate=True), Output('btn-save', 'disabled', allow_duplicate=True)],
    [Input('btn-save', 'n_clicks'), Input('btn-dup-exp', 'n_clicks'), Input('btn-del-exp', 'n_clicks'), Input('btn-activate', 'n_clicks')],
    [State('experiments-grid', 'selectedRows'), State('experiments-grid', 'rowData'), State('store-unit-data', 'data')],
    prevent_initial_call=True
)
def handle_actions(n_s, n_dup, n_del, n_act, selected, row_data, unit_json):
    trigger = ctx.triggered_id
    if not unit_json: return no_update, no_update, no_update
    ctx_data = unit_json.get('_context', {})
    params = (ctx_data.get('product'), ctx_data.get('bucket'), ctx_data.get('unit'), ctx_data.get('platform', 'AP'))
    
    msg, icon = "", "info"
    success = False
    
    try:
        if trigger == 'btn-save':
            success, msg = ExperimentService.update_experiments(params[0], params[1], params[2], row_data, params[3])
            icon = "success" if success else "danger"
            
        elif trigger == 'btn-dup-exp' and selected:
            success, msg = ExperimentService.duplicate_experiments(params[0], params[1], params[2], [r['Experiment'] for r in selected], params[3])
            icon = "success" if success else "danger"
            
        elif trigger == 'btn-del-exp' and selected:
            success, msg = ExperimentService.delete_experiments(params[0], params[1], params[2], [r['Experiment'] for r in selected], params[3])
            icon = "success" if success else "danger"
            
        elif trigger == 'btn-activate' and selected:
            success, msg = ExperimentService.activate_experiments(params[0], params[1], params[2], [r['Experiment'] for r in selected], params[3])
            icon = "success" if success else "danger"
            icon = "success" if success else "danger"
            
    except Exception as e: msg, icon = str(e), "danger"
    
    return dbc.Toast(msg, icon=icon, duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), int(time.time()), True

# 8A. Auto-Population (Open Modal)
@callback(
    [Output('modal-recipe-builder', 'is_open'),
     Output('rb-Visual_ID', 'value'),
     Output('rb-Bucket', 'value'),
     Output('rb-Check_Core', 'value'),
     Output('rb-Configuration_Mask', 'value')],
    
    Input('btn-add-exp', 'n_clicks'),
    Input('btn-edit-exp', 'n_clicks'),
    Input('btn-cancel-recipe', 'n_clicks'),
    Input('btn-create-recipe', 'n_clicks'), # Close on create (handled via logic below)
    State('store-unit-data', 'data'),
    State('experiments-grid', 'selectedRows'),
    prevent_initial_call=True
)
def open_recipe_modal(n_add, n_edit, n_cancel, n_create, unit_json, selected_rows):
    trigger = ctx.triggered_id
    
    if trigger == 'btn-cancel-recipe' or trigger == 'btn-create-recipe':
        return False, no_update, no_update, no_update, no_update
        
    if trigger == 'btn-add-exp' and unit_json:
        config = unit_json.get('Config', {})
        ctx_data = unit_json.get('_context', {})
        
        vid = config.get('Visual ID', ctx_data.get('unit', ''))
        bucket = ctx_data.get('bucket', '')
        
        # Determine Check Core
        phy_core = config.get('Victim_Phy_Core', [0])
        check_core = str(phy_core[0]) if isinstance(phy_core, list) and phy_core else str(phy_core)
        
        return True, vid, bucket, check_core, "" # Config Mask default empty

    if trigger == 'btn-edit-exp' and unit_json and selected_rows:
        exp = selected_rows[0]
        recipe = exp.get('RecipeData', {})
        
        vid = recipe.get('Visual ID', '')
        bucket = recipe.get('Bucket', '')
        check_core = recipe.get('Check Core', '')
        mask = recipe.get('Configuration (Mask)', '')
        
        # NOTE: To fully support Edit, we'd need to add MANY more Outputs to this callback.
        # However, we can use a simpler approach: add a Store for 'edit-mode-data'
        # and use separate callbacks to populate all fields if that store is not null.
        return True, vid, bucket, check_core, mask

    return no_update, no_update, no_update, no_update, no_update

# 8B. Create Experiment (Save)
@callback(
    [Output('dash-toast-anchor', 'children', allow_duplicate=True),
     Output('store-refresh-trigger', 'data', allow_duplicate=True)],
    
    Input('btn-create-recipe', 'n_clicks'),
    
    # --- FORM STATES ---
    State('rb-Experiment', 'value'), State('rb-Test_Name', 'value'), 
    State('rb-Test_Mode', 'value'), State('rb-Test_Type', 'value'),
    State('rb-COM_Port', 'value'), State('rb-IP_Address', 'value'),
    State('rb-TTL_Folder', 'value'), State('rb-Scripts_File', 'value'), State('rb-Post_Process', 'value'),
    
    State('rb-Content', 'value'), State('rb-Script', 'value'),
    State('rb-Custom_Script_Name', 'value'), State('rb-Custom_Script_Path', 'value'),
    State('rb-Pass_String', 'value'), State('rb-Fail_String', 'value'),
    State('rb-Test_Number', 'value'), State('rb-Test_Time', 'value'),
    
    State('rb-Reset', 'value'), State('rb-FastBoot', 'value'), State('rb-Reset_on_PASS', 'value'),
    State('rb-Core_License', 'value'), State('rb-600W_Unit', 'value'), State('rb-Pseudo_Config', 'value'), 
    State('rb-Disable_2_Cores', 'value'), State('rb-Configuration_Mask', 'value'), State('rb-Boot_Breakpoint', 'value'), 
    State('rb-Check_Core', 'value'),
    
    # Voltage
    State('rb-Voltage_Type', 'value'), State('rb-Voltage_IA', 'value'), State('rb-Voltage_CFC', 'value'),
    State('rb-Loops', 'value'), State('rb-Frequency_IA', 'value'), State('rb-Frequency_CFC', 'value'),
    
    # Sweep
    State('rb-Sweep_Type', 'value'), State('rb-Sweep_Domain', 'value'), State('rb-ShmooFile', 'value'),
    State('rb-Start', 'value'), State('rb-End', 'value'), State('rb-Steps', 'value'), State('rb-ShmooLabel', 'value'),
    
    # Linux (Extended)
    State('rb-Startup_Linux', 'value'), State('rb-Linux_Pre_Command', 'value'), State('rb-Linux_Pass_String', 'value'),
    State('rb-Linux_Content_Wait_Time', 'value'), 
    State('rb-Linux_Content_Line_0', 'value'), State('rb-Linux_Content_Line_1', 'value'),
    State('rb-Linux_Path', 'value'), State('rb-Linux_Post_Command', 'value'), State('rb-Linux_Fail_String', 'value'),
    State('rb-Linux_Content_Line_2', 'value'), State('rb-Linux_Content_Line_3', 'value'),
    State('rb-Linux_Content_Line_4', 'value'), State('rb-Linux_Content_Line_5', 'value'),

    # Dragon (Extended)
    State('rb-Startup_Dragon', 'value'), State('rb-ULX_Path', 'value'), State('rb-VVAR0', 'value'), State('rb-VVAR2', 'value'),
    State('rb-VVAR_EXTRA', 'value'), State('rb-Dragon_Pre_Command', 'value'), 
    State('rb-Merlin_Name', 'value'), State('rb-Merlin_Drive', 'value'),
    State('rb-Dragon_Content_Path', 'value'), State('rb-Dragon_Content_Line', 'value'),
    State('rb-Merlin_Path', 'value'), State('rb-VVAR1', 'value'), State('rb-VVAR3', 'value'), 
    State('rb-Dragon_Post_Command', 'value'), State('rb-Stop_on_Fail', 'value'),
    
    State('store-unit-data', 'data'),
    prevent_initial_call=True
)
def create_new_experiment(n_create, 
                       exp_en, test_name, test_mode, test_type,
                       com, ip, ttl, scripts, post,
                       content, script, cust_name, cust_path, pass_str, fail_str, test_num, test_time,
                       reset, fastboot, reset_pass, core_lic, unit_600, pseudo, dis_2_cores, config_mask, boot_bkp, check_core,
                       volt_type, volt_ia, volt_cfc, loops, freq_ia, freq_cfc,
                       sweep_type, sweep_dom, shmoo_file, start, end, steps, shmoo_lbl,
                       lin_start, lin_pre, lin_pass, lin_wait, lin_l0, lin_l1, lin_path, lin_post, lin_fail, lin_l2, lin_l3, lin_l4, lin_l5,
                       drag_start, ulx, vvar0, vvar2, vvar_extra, drag_pre, merlin_nm, merlin_dr, drag_cont, drag_line, merlin, vvar1, vvar3, drag_post, stop_fail,
                       unit_json):
    
    if not n_create or not unit_json: return no_update, no_update
    
    # Construct Form Data Dictionary
    form_data = {
        "Experiment": exp_en, "Test Name": test_name, "Test Mode": test_mode, "Test Type": test_type,
        "COM Port": com, "IP Address": ip, "TTL Folder": ttl, "Scripts File": scripts, "Post Process": post,
        "Content": content, 
        "Pass String": pass_str, "Fail String": fail_str, "Test Number": test_num, "Test Time": test_time,
        "Reset": reset, "FastBoot": fastboot, "Reset on PASS": reset_pass, "Core License": core_lic,
        "600W Unit": unit_600, "Pseudo Config": pseudo, "Disable 2 Cores": dis_2_cores,
        "Configuration (Mask)": config_mask, "Boot Breakpoint": boot_bkp, "Check Core": check_core,
        
        # Tech Specs
        "Voltage Type": volt_type, "Voltage IA": volt_ia, "Voltage CFC": volt_cfc,
        "Loops": loops, "Frequency IA": freq_ia, "Frequency CFC": freq_cfc,
        
        # Sweep Params
        "Sweep Type": sweep_type, "Sweep Domain": sweep_dom, "ShmooFile": shmoo_file,
        "Start": start, "End": end, "Steps": steps, "ShmooLabel": shmoo_lbl,
        
        # Linux
        "Startup Linux": lin_start, "Linux Pre Command": lin_pre, "Linux Pass String": lin_pass, 
        "Linux Content Wait Time": lin_wait,
        "Linux Content Line 0": lin_l0, "Linux Content Line 1": lin_l1, "Linux Content Line 2": lin_l2, 
        "Linux Path": lin_path, "Linux Post Command": lin_post, "Linux Fail String": lin_fail,
        "Linux Content Line 3": lin_l3, "Linux Content Line 4": lin_l4, "Linux Content Line 5": lin_l5,
        
        # Dragon
        "Startup Dragon": drag_start, "ULX Path": ulx, "VVAR0": vvar0, "VVAR2": vvar2, "VVAR_EXTRA": vvar_extra,
        "Dragon Pre Command": drag_pre, "Merlin Name": merlin_nm, "Merlin Drive": merlin_dr,
        "Dragon Content Path": drag_cont, "Dragon Content Line": drag_line, "Merlin Path": merlin, 
        "VVAR1": vvar1, "VVAR3": vvar3, "Dragon Post Command": drag_post, "Stop on Fail": stop_fail
    }

    # Call Service
    success, msg, timestamp = ExperimentService.process_experiment(unit_json, form_data)
    
    icon = "success" if success else "danger"
    toast = dbc.Toast(msg, icon=icon, duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom")
    
    return toast, timestamp

# 8C. Test Name Validation & Suggestions
@callback(
    [Output('rb-validation-msg', 'children'), 
     Output('btn-create-recipe', 'disabled'),
     Output('rb-Configuration_Mask', 'value', allow_duplicate=True)],
    [Input('rb-Test_Name', 'value'), 
     Input('rb-Test_Mode', 'value'),
     Input('rb-Check_Core', 'value'),
     Input('rb-Content', 'value'),
     Input('rb-Test_Type', 'value')],
    [State('store-unit-data', 'data')],
    prevent_initial_call=True
)
def validate_test_form(test_name, test_mode, check_core, content, test_type, unit_json):
    if not unit_json: return "", True, no_update
    
    msg = ""
    disabled = False
    new_mask = no_update
    
    # 1. Critical Fields Empty
    if not test_name or not check_core:
        disabled = True
        if not test_name: msg = "⚠ Test Name is required."
    
    # 2. Character Validation
    invalid_chars = [',', '.', ';', ':', '!', '?', '*', '"', '<', '>', '|', '\\', '/']
    if test_name and any(c in test_name for c in invalid_chars):
        msg = "⚠ Invalid characters in name (no . , / etc.)"
        disabled = True

    # 3. Uniqueness Check
    existing_exps = unit_json.get('experiments', [])
    if test_name and any(e.get('Experiment') == test_name for e in existing_exps):
        msg = "⚠ Test Name already exists in this unit."
        disabled = True

    # 4. Slice/Mesh Mode Automation
    if test_mode == "Slice":
        new_mask = check_core
    elif test_mode == "Mesh":
        new_mask = ""
        
    return msg, disabled, new_mask

# 8D. Auto-suggest Name
@callback(
    Output('rb-Test_Name', 'value', allow_duplicate=True),
    [Input('rb-Content', 'value'), Input('rb-Test_Type', 'value'), Input('rb-Script', 'value')],
    prevent_initial_call=True
)
def suggest_test_name(content, test_type, script):
    ts = int(time.time()) % 10000
    return f"{content}_{test_type}_{script}_{ts}"

# 9. Clientside Logic (Clean Implementation)
dash.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='display_if_loops'),
    Output('section-voltage', 'style'),
    Input('rb-Test_Type', 'value')
)

dash.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='display_if_sweep'),
    Output('section-sweep', 'style'),
    Input('rb-Test_Type', 'value')
)

dash.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='display_if_custom'),
    Output('section-custom-script', 'style'),
    Input('rb-Script', 'value')
)

dash.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='display_if_linux'),
    Output('section-linux', 'style'),
    Input('rb-Content', 'value')
)

dash.clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='display_if_dragon'),
    Output('section-dragon', 'style'),
    Input('rb-Content', 'value')
)

# 10. Recipe Viewer Logic
@callback(
    [Output('modal-recipe-viewer', 'is_open'),
     Output('recipe-viewer-content', 'children')],
    Input('btn-view-recipe', 'n_clicks'),
    Input('btn-close-viewer', 'n_clicks'),
    State('experiments-grid', 'selectedRows'),
    prevent_initial_call=True
)
def handle_recipe_viewer(n_view, n_close, selected_rows):
    trigger = ctx.triggered_id
    if trigger == 'btn-close-viewer':
        return False, no_update
        
    if trigger == 'btn-view-recipe' and selected_rows and len(selected_rows) > 0:
        recipe_data = selected_rows[0].get('RecipeData', {})
        content = json.dumps(recipe_data or selected_rows[0], indent=2)
        return True, content
    return no_update, no_update

# 11. Placeholder Load Data
@callback(Output('dash-toast-anchor', 'children', allow_duplicate=True), Input('btn-load-data', 'n_clicks'), prevent_initial_call=True)
def simulate_load(n):
    if not n: return no_update
    time.sleep(1.5)
    return dbc.Toast("Data synchronized.", icon="success", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom")

# 12. Unit Creation Logic
@callback(
    [Output('modal-unit-creator', 'is_open'),
     Output('sel-unit', 'options', allow_duplicate=True),
     Output('dash-toast-anchor', 'children', allow_duplicate=True),
     Output('new-unit-product', 'options')], # Refresh products in Unit Creator
    [Input('btn-open-unit-modal', 'n_clicks'),
     Input('btn-cancel-unit', 'n_clicks'),
     Input('btn-create-unit', 'n_clicks')],
    [State('new-unit-product', 'value'),
     State('new-unit-bucket', 'value'),
     State('new-unit-vid', 'value'),
     State('new-unit-platform', 'value'),
     State('new-unit-qdf', 'value'),
     State('sel-product', 'value'), State('sel-bucket', 'value'), State('sel-platform', 'value')],
    prevent_initial_call=True
)
def handle_create_unit(n_open, n_cancel, n_create, n_prod, n_buck, n_vid, n_plat, n_qdf, curr_prod, curr_buck, curr_plat):
    trigger = ctx.triggered_id
    
    if trigger == 'btn-open-unit-modal':
        prods = UnitService.get_products()
        prod_opts = [{'label': p, 'value': p} for p in prods]
        return True, no_update, no_update, prod_opts
        
    if trigger == 'btn-cancel-unit':
        return False, no_update, no_update, no_update
        
    if trigger == 'btn-create-unit':
        if not (n_prod and n_buck and n_vid):
             return True, no_update, dbc.Toast("Missing fields", icon="warning", duration=3000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
             
        success, msg = UnitService.create_unit(n_prod, n_buck, n_vid, n_plat, n_qdf)
        
        if success:
             # Refresh units if we are in the same context
             new_opts = no_update
             if n_prod == curr_prod and n_buck == curr_buck and n_plat == curr_plat:
                 units = UnitService.get_units(curr_prod, curr_buck, curr_plat)
                 new_opts = [{'label': u, 'value': u} for u in units]
                 
             return False, new_opts, dbc.Toast("Unit Created.", icon="success", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
        else:
             return True, no_update, dbc.Toast(msg, icon="danger", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update

    return no_update, no_update, no_update, no_update

# 13. Script Template Management & Mapping
@callback(
    Output('rb-Script', 'options'),
    [Input('store-refresh-trigger', 'data'), Input('modal-recipe-builder', 'is_open')]
)
def update_script_options(trigger, is_open):
    configs = DataHandler.get_script_configs()
    return [{'label': k, 'value': k} for k in configs.keys()]

@callback(
    Output('rb-Scripts_File', 'value'),
    Input('rb-Script', 'value'),
    prevent_initial_call=True
)
def map_script_to_path(template_name):
    if not template_name: return no_update
    configs = DataHandler.get_script_configs()
    return configs.get(template_name, "")

# 14. Script Manager Modal
@callback(
    [Output('modal-script-manager', 'is_open'), 
     Output('script-modal-msg', 'children'),
     Output('store-refresh-trigger', 'data', allow_duplicate=True)],
    [Input('btn-open-script-modal', 'n_clicks'), Input('btn-cancel-script', 'n_clicks'), Input('btn-save-script', 'n_clicks')],
    [State('new-script-name', 'value'), State('new-script-path', 'value')],
    prevent_initial_call=True
)
def handle_script_manager(n_open, n_cancel, n_save, name, path):
    trigger = ctx.triggered_id
    if trigger == 'btn-open-script-modal': return True, ""
    if trigger == 'btn-cancel-script': return False, ""
    if trigger == 'btn-save-script':
        if not name or not path: return True, "Missing name or path", no_update
        success, msg = DataHandler.save_script_config(name, path)
        if success: return False, "", datetime.datetime.now().isoformat()
        return True, msg, no_update
    return no_update, no_update, no_update

# 15. Product / Bucket Creation Logic
@callback(
    [Output('modal-product-creator', 'is_open'), Output('prod-modal-msg', 'children'), Output('sel-product', 'options', allow_duplicate=True)],
    [Input('btn-open-prod-modal', 'n_clicks'), Input('btn-open-prod-modal-2', 'n_clicks'), Input('btn-cancel-prod', 'n_clicks'), Input('btn-create-prod', 'n_clicks')],
    State('new-prod-name', 'value'),
    prevent_initial_call=True
)
def handle_prod_creator(n_open, n_open2, n_cancel, n_create, name):
    trigger = ctx.triggered_id
    if trigger in ['btn-open-prod-modal', 'btn-open-prod-modal-2']: return True, "", no_update
    if trigger == 'btn-cancel-prod': return False, "", no_update
    if trigger == 'btn-create-prod':
        if not name: return True, "Name required", no_update
        success, msg = UnitService.create_product(name)
        if success:
            prods = UnitService.get_products()
            return False, "", [{'label': p, 'value': p} for p in prods]
        return True, msg, no_update
    return no_update, no_update, no_update

@callback(
    [Output('modal-bucket-creator', 'is_open'), Output('buck-modal-msg', 'children'), Output('new-buck-parent', 'options')],
    [Input('btn-open-buck-modal', 'n_clicks'), Input('btn-open-buck-modal-2', 'n_clicks'), Input('btn-cancel-buck', 'n_clicks'), Input('btn-create-buck', 'n_clicks')],
    [State('new-buck-name', 'value'), State('new-buck-parent', 'value')],
    prevent_initial_call=True
)
def handle_buck_creator(n_open, n_open2, n_cancel, n_create, name, parent):
    trigger = ctx.triggered_id
    if trigger in ['btn-open-buck-modal', 'btn-open-buck-modal-2']:
        prods = UnitService.get_products()
        opts = [{'label': p, 'value': p} for p in prods]
        return True, "", opts
    if trigger == 'btn-cancel-buck': return False, "", no_update
    if trigger == 'btn-create-buck':
        # Validation delegated implicitly or check here
        if not name or not parent: return True, "Name and Parent required", no_update
        success, msg = UnitService.create_bucket(parent, name)
        if success: return False, "", no_update
        return True, msg, no_update
    return no_update, no_update, no_update

# 16. MRS Editing Logic
@callback(
    [Output('dash-toast-anchor', 'children', allow_duplicate=True),
     Output('store-refresh-trigger', 'data', allow_duplicate=True)],
    Input('btn-save-mrs', 'n_clicks'),
    [State('edit-mrs-value', 'value'),
     State('sel-product', 'value'),
     State('sel-bucket', 'value'),
     State('sel-unit', 'value'),
     State('sel-platform', 'value')],
    prevent_initial_call=True
)
def handle_mrs_update(n_clicks, new_mrs, prod, buck, unit, plat):
    if not n_clicks: return no_update, no_update
    if not all([prod, buck, unit, plat, new_mrs]):
        return dbc.Toast("Missing data for MRS update", icon="danger", duration=3000), no_update
        
    success, msg = DataHandler.update_unit_mrs(prod, buck, unit, plat, new_mrs)
    if success:
        return dbc.Toast("MRS Updated & Date Refreshed.", icon="success", duration=3000), datetime.datetime.now().isoformat()
    else:
        return dbc.Toast(f"Update failed: {msg}", icon="danger", duration=3000), no_update

# 17. Recipe (Template) Logic
@callback(
    [Output('modal-save-recipe', 'is_open'),
     Output('dash-toast-anchor', 'children', allow_duplicate=True)],
    Input('btn-open-save-recipe', 'n_clicks'),
    State('experiments-grid', 'selectedRows'),
    prevent_initial_call=True
)
def open_save_recipe_modal(n_open, selected):
    if not selected: 
        return False, dbc.Toast("Select experiments first.", icon="warning", duration=3000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom")
    return True, no_update

@callback(
    [Output('modal-save-recipe', 'is_open', allow_duplicate=True),
     Output('dash-toast-anchor', 'children', allow_duplicate=True)],
    [Input('btn-cancel-save-recipe', 'n_clicks'),
     Input('btn-confirm-save-recipe', 'n_clicks')],
    [State('new-recipe-name', 'value'),
     State('experiments-grid', 'selectedRows')],
    prevent_initial_call=True
)
def handle_save_recipe(n_cancel, n_save, name, selected):
    trigger = ctx.triggered_id
    if trigger == 'btn-cancel-save-recipe':
        return False, no_update
        
    if trigger == 'btn-confirm-save-recipe':
        if not name:
             return True, dbc.Toast("Name is required", icon="warning", duration=3000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom")
             
        success, msg = TemplateService.save_template(name, selected)
        icon = "success" if success else "danger"
        return not success, dbc.Toast(msg, icon=icon, duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom")
        
    return no_update, no_update

@callback(
    [Output('modal-load-recipe', 'is_open'),
     Output('select-recipe-dropdown', 'options')],
    Input('btn-open-load-recipe', 'n_clicks'),
    prevent_initial_call=True
)
def open_load_recipe_modal(n_open):
    templates = TemplateService.get_templates()
    opts = [{'label': t, 'value': t} for t in templates]
    return True, opts

@callback(
    [Output('modal-load-recipe', 'is_open', allow_duplicate=True),
     Output('dash-toast-anchor', 'children', allow_duplicate=True),
     Output('store-refresh-trigger', 'data', allow_duplicate=True)],
    [Input('btn-cancel-load-recipe', 'n_clicks'),
     Input('btn-confirm-load-recipe', 'n_clicks')],
    [State('select-recipe-dropdown', 'value'),
     State('store-unit-data', 'data')],
    prevent_initial_call=True
)
def handle_load_recipe(n_cancel, n_load, recipe_name, unit_data):
    try:
        trigger = ctx.triggered_id
        if trigger == 'btn-cancel-load-recipe':
            return False, no_update, no_update
            
        if trigger == 'btn-confirm-load-recipe':
            if not recipe_name:
                 return True, dbc.Toast("Select a recipe", icon="warning", duration=3000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
                 
            # Load Template
            tmpl_exps, msg = TemplateService.load_template(recipe_name)
            if not tmpl_exps:
                 return True, dbc.Toast(msg, icon="danger", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
                 
            # Apply to Unit (Memory)
            success, msg = TemplateService.apply_template_to_unit(unit_data, tmpl_exps)
            if not success:
                 return True, dbc.Toast(msg, icon="danger", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
                 
            # Save Unit (Disk)
            ctx_data = unit_data.get('_context', {})
            prod = ctx_data.get('product')
            buck = ctx_data.get('bucket')
            unit = ctx_data.get('unit')
            plat = ctx_data.get('platform', 'AP')
            
            # We can use ExperimentService.update_experiments because apply_template_to_unit updated unit_data['experiments']
            save_success, save_msg = ExperimentService.update_experiments(prod, buck, unit, unit_data['experiments'], plat)
            
            if save_success:
                 return False, dbc.Toast(msg, icon="success", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), int(time.time())
            else:
                 return True, dbc.Toast(save_msg, icon="danger", duration=4000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
                 
        return no_update, no_update, no_update
    except Exception as e:
        import traceback
        return True, dbc.Toast(f"Error: {str(e)}", icon="danger", duration=5000, is_open=True, style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999}, className="toast-custom"), no_update
