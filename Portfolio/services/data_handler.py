import os
import json
import logging
import datetime
from config import PRODUCTS_DIR

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings')
SCRIPTS_CONFIG_PATH = os.path.join(SETTINGS_DIR, 'scripts_config.json')

class DataHandler:
    @staticmethod
    def get_products():
        if not os.path.exists(PRODUCTS_DIR): return []
        # List directories in data/, excluding any that start with '.' or 'settings'
        return [d for d in os.listdir(PRODUCTS_DIR) 
                if os.path.isdir(os.path.join(PRODUCTS_DIR, d)) and not d.startswith('.') and d != 'settings']

    @staticmethod
    def get_buckets(product):
        path = os.path.join(PRODUCTS_DIR, product, 'Buckets')
        if not os.path.exists(path): return []
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    @staticmethod
    def get_units(product, bucket, platform='AP'):
        path = os.path.join(PRODUCTS_DIR, product, 'Buckets', bucket, 'Results_Data', 'Units', platform)
        if not os.path.exists(path): return []
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    @staticmethod
    def get_unit_path(product, bucket, unit, platform='AP'):
        return os.path.join(PRODUCTS_DIR, product, 'Buckets', bucket, 'Results_Data', 'Units', platform, unit, f"{unit}_Debug_Results_Plain.json")

    @staticmethod
    def load_unit_data(product, bucket, unit, platform='AP'):
        path = DataHandler.get_unit_path(product, bucket, unit, platform)
        if not os.path.exists(path):
            return None, "File not found"
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data, "Success"
        except Exception as e:
            return None, str(e)

    @staticmethod
    def save_unit_data(product, bucket, unit, data, platform='AP'):
        path = DataHandler.get_unit_path(product, bucket, unit, platform)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True, "Saved successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_unit(product, bucket, unit, platform='AP', qdf="UNK"):
        path = os.path.join(PRODUCTS_DIR, product, 'Buckets', bucket, 'Results_Data', 'Units', platform, unit)
        file_path = os.path.join(path, f"{unit}_Debug_Results_Plain.json")
        
        try:
            os.makedirs(path, exist_ok=True)
            
            # Initial Template
            data = {
                "Config": {
                    "Visual ID": unit,
                    "QDF": qdf,
                    "MRS": "Created Manually",
                    "Victim_Phy_Core": [0]
                },
                "experiments": []
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            return True, "Unit created"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def activate_experiments(product, bucket, unit, exp_names, platform='AP'):
        data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
        if not data: return False, msg
        
        selected_exps = [e for e in data.get("experiments", []) if e.get("Experiment") in exp_names]
        pending_exps = [e for e in selected_exps if e.get("Estado") == "Pending"]
        
        if not pending_exps:
            return False, "No 'Pending' experiments selected"
            
        import datetime
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        date_str = now.strftime("%Y%m%d")
        
        recipe_dict = {}
        step_idx = 1
        
        # Grouping for Sweeps
        sweep_groups = {} # test_name -> list of exp_data
        other_exps = []
        
        for exp in pending_exps:
            rd = exp.get("RecipeData", {})
            t_type = rd.get("Test Type", "Loops")
            t_name = rd.get("Test Name", exp.get("Experiment"))
            
            if t_type == "Sweep":
                if t_name not in sweep_groups:
                    sweep_groups[t_name] = []
                sweep_groups[t_name].append(exp)
            else:
                other_exps.append(exp)
        
        # 1. Process Consolidated Sweeps
        for t_name, group in sweep_groups.items():
            # Use the first one as a template
            base_rd = group[0].get("RecipeData", {}).copy()
            
            # Reset individual points to null for the Framework sweep consumption
            base_rd["Voltage IA"] = None
            base_rd["Voltage CFC"] = None
            base_rd["Frequency IA"] = None
            base_rd["Frequency CFC"] = None
            
            recipe_dict[f"step_{step_idx}"] = base_rd
            step_idx += 1
            
        # 2. Process Other Experiments
        for exp in other_exps:
            recipe_dict[f"step_{step_idx}"] = exp.get("RecipeData", {})
            step_idx += 1
            
        # 3. Save Recipe File
        unit_dir = os.path.dirname(DataHandler.get_unit_path(product, bucket, unit, platform))
        recipes_dir = os.path.join(unit_dir, "Recipes")
        os.makedirs(recipes_dir, exist_ok=True)
        
        recipe_filename = f"{unit}_{date_str}_{timestamp}.json"
        recipe_path = os.path.join(recipes_dir, recipe_filename)
        
        try:
            with open(recipe_path, 'w', encoding='utf-8') as f:
                json.dump(recipe_dict, f, indent=4)
                
            # 4. Update Status in unit data
            for exp in data["experiments"]:
                if exp.get("Experiment") in exp_names and exp.get("Estado") == "Pending":
                    exp["Estado"] = "Running"
                    exp["Link"] = f"Recipes/{recipe_filename}"
                    
            DataHandler.save_unit_data(product, bucket, unit, data, platform)
            return True, f"Recipe generated: {recipe_filename}. {step_idx-1} steps total."
        except Exception as e:
            return False, f"Error saving recipe: {str(e)}"

    @staticmethod
    def update_experiment_status(product, bucket, unit, exp_name, new_status, platform='AP'):
        data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
        if not data: return False, msg
        
        found = False
        for exp in data.get("experiments", []):
            if exp.get("Experiment") == exp_name:
                exp["Estado"] = new_status
                found = True
                break
        
        if found:
            return DataHandler.save_unit_data(product, bucket, unit, data, platform)
        return False, "Experiment not found"

    @staticmethod
    def duplicate_experiments(product, bucket, unit, exp_names, platform='AP'):
        data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
        if not data: return False, msg
        
        current_exps = data.get("experiments", [])
        new_exps = []
        
        for name in exp_names:
            original = next((e for e in current_exps if e.get("Experiment") == name), None)
            if not original: continue
            
            copy_exp = original.copy()
            base_name = f"{name}_Copy"
            new_name = base_name
            
            # Ensure unique name
            idx = 1
            while any(e.get("Experiment") == new_name for e in current_exps + new_exps):
                new_name = f"{base_name}_{idx}"
                idx += 1
            
            copy_exp["Experiment"] = new_name
            copy_exp["Estado"] = "Pending"
            copy_exp["FailRate"] = 0
            new_exps.append(copy_exp)
            
        if not new_exps: return False, "No experiments duplicated"
        
        data["experiments"].extend(new_exps)
        return DataHandler.save_unit_data(product, bucket, unit, data, platform)

            
        return DataHandler.save_unit_data(product, bucket, unit, data, platform)

    @staticmethod
    def get_script_configs():
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        if not os.path.exists(SCRIPTS_CONFIG_PATH):
            default = {"Baseline": ""}
            with open(SCRIPTS_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=4)
            return default
        try:
            with open(SCRIPTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"Baseline": ""}

    @staticmethod
    def save_script_config(name, path):
        configs = DataHandler.get_script_configs()
        configs[name] = path
        try:
            with open(SCRIPTS_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=4)
            return True, "Config saved"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_product(product_name):
        path = os.path.join(PRODUCTS_DIR, product_name)
        try:
            os.makedirs(os.path.join(path, 'Buckets'), exist_ok=True)
            return True, f"Product {product_name} created"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_bucket(product, bucket_name):
        path = os.path.join(PRODUCTS_DIR, product, 'Buckets', bucket_name)
        try:
            # Create standard subdirs
            os.makedirs(os.path.join(path, 'Results_Data', 'Units', 'AP'), exist_ok=True)
            os.makedirs(os.path.join(path, 'Results_Data', 'Units', 'SP'), exist_ok=True)
            return True, f"Bucket {bucket_name} created under {product}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def update_unit_mrs(product, bucket, unit, platform, new_mrs):
        success, data = DataHandler.get_unit_data(product, bucket, unit, platform)
        if not success: return False, data
        
        config = data.get("Config", {})
        config["MRS"] = new_mrs
        config["MRS_Entry_Date"] = datetime.datetime.now().strftime("%m/%d/%Y")
        config["MRS_Days_Remaining"] = 180 # Reset to max on new entry
        
        data["Config"] = config
        return DataHandler.save_unit_data(product, bucket, unit, data, platform)
