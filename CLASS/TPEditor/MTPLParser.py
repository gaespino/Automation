import json
import os

def parse_mptl_file(file_path, search_word, lut_values, default_values):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    found_section = False
    section_data = {key: default for key, default in default_values.items()}  # Initialize with default values
    is_multi_trial_test = False

    for line in lines:
        line = line.strip()

        # Check if the line contains the search word in the correct format
        if line.startswith("Test ") or line.startswith("MultiTrialTest "):
            if search_word in line:
                found_section = True
                is_multi_trial_test = line.startswith("MultiTrialTest ")
                continue

        # If the section is found, start collecting data
        if found_section:
            if line.startswith("}"):
                # End of the section
                break

            # Extract key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip(';').strip('"')

                # Check if the key is in the lookup values
                if key in lut_values:
                    section_data[key] = value

    # Add Bin_Matrix if it's a MultiTrialTest
    if is_multi_trial_test:
        section_data['Bin_Matrix'] = ['7911', '7912', '7913', '7914']

    # Return section data only if the section was found
    return section_data if found_section else None

def uncore_regression():
    base_dict = {}
    FREQ = ['F1', 'F2', 'F4']

    # Building All cases, some Instances might not be available in all Frequencies
    for F in FREQ:
        uncore_instances = {
            f'DRG_{F}_CD0': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD0',
            f'DRG_{F}_CD1': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD1',
            f'DRG_{F}_CD2': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHDRGCD2',
            f'UUFC_{F}_PARALLEL': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTWPARALLEL',
            f'UUFC_{F}_CFC_MESHTW': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTW',
            f'UUFC_{F}_HDC_MESHTW': f'FUN_UNCORE_COMP::UNCORE_HDC_VMIN_K_CHKCFCHDC{F}_STF_HDC_VMIN_{F}_MESHTW',
            f'UUFC_{F}_MESHTWK': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDC{F}_STF_CFCHDC_VMIN_{F}_MESHTWK', #UNCORE_CFC_VMIN_K_CHKCFCHDCF1_STF_CFCHDC_VMIN_F1_MESHTWK
            f'FCTRACKINGA_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGA',
            f'FCTRACKINGB_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGB',
            f'FCTRACKINGC_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGC',
            f'FCTRACKINGD_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGD',
            f'FCTRACKINGE_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGE',
            f'FCTRACKINGF_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGF',
            f'FCTRACKINGG_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGG',
            f'FCTRACKINGH_{F}': f'FUN_UNCORE_COMP::UNCORE_COMP_STRUCTURETRACKER_K_CHKCFCHDC{F}_X_X_X_X_FCTRACKINGH',
            f'PATMODS_CD0{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_DRGCD0',
            f'PATMODS_CD1{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_DRGCD1',
            f'PATMODS_CD2{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_DRGCD2',
            f'PATMODS_ROWS0{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_ENROWDPM',
            f'PATMODS_ROWS1{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_ENROWDPM1',
            f'PATMODS_ROWS2{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_ENROWDPM2',
            f'PATMODS_HTDIS{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_HTDIS',
            f'PATMODS_HTEN{F}': f'FUN_UNCORE_COMP::UNCORE_CFC_PATMOD_K_CHKCFCHDC{F}_X_CFCHDC_X_{F}_HTEN',
        }

        base_dict.update(uncore_instances)

    F = 'F4'
    dragon_f4 = {
        f'DRG_F4_DRGPSEUDO': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_DRGPSEUDOSBFT',
        f'DRG_F4_DRGPSEUDO1': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_DRGPSEUDOSBFT1',
        f'DRG_F4_DRGPSEUDO2': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_DRGPSEUDOSBFT2',
        f'DRG_F4_ROWDRGPSEUDOSBFT': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_ROWDRGPSEUDOSBFT',
        f'DRG_F4_ROWDRGPSEUDOSBFT1': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_ROWDRGPSEUDOSBFT1',
        f'DRG_F4_ROWDRGPSEUDOSBFT2': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_ROWDRGPSEUDOSBFT2',
        f'DRG_F4_ROWPSEUDODPM': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_ROWPSEUDODPM',
        f'DRG_F4_ROWPSEUDODPM1': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_ROWPSEUDODPM1',
        f'DRG_F4_ROWPSEUDODPM2': f'FUN_UNCORE_COMP::UNCORE_CFC_VMIN_K_CHKCFCHDCF4_STF_CFCHDC_VMIN_F4_ROWPSEUDODPM2',
    }

    base_dict.update(dragon_f4)

    return base_dict

def generate_default_mtpl_data(file_path, output_dir):
    instances = uncore_regression()
    default_mtpl_data = {}

    content_lut = {'BypassPort': '1', 'LogLevel': 'Disabled', 'Patlist': None, 'ShmooEnable': 'DISABLED', 'ShmooConfigurationFile': None}
    fctracking_lut = {'BypassPort': '1', 'ConfigFile': None}
    patmods_lut = {'BypassPort': '1', 'ConfigurationFile': None, 'SetPoint': None}

    for instance_name, instance_word in instances.items():
        search_word = instance_word.split('::')[1]
        if 'FCTRACKING' in search_word:
            lut_values = fctracking_lut.keys()
            default_values = fctracking_lut
        elif 'PATMOD' in search_word:
            lut_values = patmods_lut.keys()
            default_values = patmods_lut
        else:
            lut_values = content_lut.keys()
            default_values = content_lut

        section_data = parse_mptl_file(file_path, search_word, lut_values, default_values)
        if section_data:
            default_mtpl_data[instance_word] = section_data

    # Get the parent directory name to use as the JSON file name
    parent_dir_name = os.path.basename(os.path.dirname(file_path))
    json_file_name = f"{parent_dir_name}.json"
    output_path = os.path.join(output_dir, json_file_name)

    # Save the data to a JSON file
    with open(output_path, 'w') as json_file:
        json.dump(default_mtpl_data, json_file, indent=4)

    print(f"{json_file_name} has been created at {output_path}.")

def process_directory_for_mptl_files(search_dir, output_dir='C:\\Temp'):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Walk through the directory to find .mptl files
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith('.mtpl'):
                file_path = os.path.join(root, file)
                generate_default_mtpl_data(file_path, output_dir)


def generate_default():
    # Example usage
    search_dir = r'I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\Modules\FUN_UNCORE_COMP'
    #mtpls_dir = r'I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\MTPLs'
    output_dir = r'I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\MTPLs\ConfigFiles'

    process_directory_for_mptl_files(search_dir, output_dir)

def generate_templates():
    # Example usage
    #search_dir = r'I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\Modules\FUN_UNCORE_COMP'
    search_dir = r'I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\MTPLs'
    output_dir = r'I:\intel\engineering\dev\user_links\ddcanale\TP\TP_WW22P4_Short\MTPLs\ConfigFiles'

    process_directory_for_mptl_files(search_dir, output_dir)


if __name__ == '__main__':
    
    #search_dir = r'I:\intel\hdmxprogs\SPARK\production\Execution\12259572\3c3e3360edca\GNRSVXXXXHX4A00S521\Modules\FUN_UNCORE_COMP'
    #output_dir = r'C:\Temp'
    #process_directory_for_mptl_files(search_dir, output_dir)
    generate_default()
    generate_templates()



