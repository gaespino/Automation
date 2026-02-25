import time
import numpy as np
import datetime
from services.data_handler import DataHandler

class ExperimentService:
    
    @staticmethod
    def validate_submission(form_data, existing_experiments):
        """Validates the experiment submission form."""
        test_name = form_data.get('Test Name')
        
        if not test_name:
            return False, "Test Name is required."
            
        invalid_chars = [',', '.', ';', ':', '!', '?', '*', '"', '<', '>', '|', '\\', '/']
        if any(c in test_name for c in invalid_chars):
            return False, "Test Name contains invalid characters."

        # Check for duplicates ONLY if we are creating new (not updating)
        # However, the current logic in dashboard says if it exists, UPDATE it.
        # So duplicate check is actually "check if we are updating or creating".
        # We'll handle that in the processing logic.
        
        return True, ""

    @staticmethod
    def process_experiment(unit_json, form_data):
        """
        Main method to process the experiment form. 
        Generates experiment dicts and saves them to the unit.
        Returns: (success, message, timestamp)
        """
        
        # 1. Validation
        valid, msg = ExperimentService.validate_submission(form_data, unit_json.get('experiments', []))
        if not valid:
            return False, msg, 0

        # 2. Extract Context
        ctx_data = unit_json.get('_context', {})
        product = ctx_data.get('product')
        bucket = ctx_data.get('bucket')
        unit = ctx_data.get('unit')
        platform = ctx_data.get('platform', 'AP')
        
        if not all([product, bucket, unit]):
            return False, "Missing unit context data.", 0

        # 3. Base Recipe Construction & Standardization
        test_mode = form_data.get('Test Mode')
        check_core = form_data.get('Check Core')
        config_mask = form_data.get('Configuration (Mask)')
        
        # Logic for Slice Mode
        final_mask = config_mask
        if test_mode == "Slice":
            final_mask = check_core

        base_recipe = form_data.copy()
        
        # --- Standardization Start ---
        
        # Inject Context
        base_recipe['Visual ID'] = unit
        base_recipe['Bucket'] = bucket
        base_recipe['Product'] = product
        base_recipe['Product Chop'] = product # Assuming Product Chop is same as Product for now
        
        # Update specific fields
        base_recipe['Configuration (Mask)'] = final_mask
        
        # Remove unwanted fields
        if 'Script/Template' in base_recipe:
            del base_recipe['Script/Template']
            
        # Ensure Scripts File is present (it should be in form_data, but let's be safe)
        if 'Scripts File' not in base_recipe:
            base_recipe['Scripts File'] = None
            
        # Type Enforcement & Null Handling
        def safe_int(val):
            try:
                if val is None or val == "": return None
                return int(float(val)) # Handle "30.0" as 30
            except (ValueError, TypeError):
                return val # Return original if fail, or maybe None? 
        
        def safe_float(val):
            try:
                if val is None or val == "": return None
                return float(val)
            except (ValueError, TypeError):
                return None # Return None if fail (e.g. for Start/End)

        # Fields to convert to INT
        int_fields = ['Test Number', 'Test Time', 'Loops', 'Check Core', 'Configuration (Mask)']
        for field in int_fields:
            if field in base_recipe:
                base_recipe[field] = safe_int(base_recipe[field])

        # Fields to convert to FLOAT
        float_fields = ['Start', 'End', 'Steps', 'Voltage IA', 'Voltage CFC', 'Frequency IA', 'Frequency CFC']
        for field in float_fields:
            if field in base_recipe:
                base_recipe[field] = safe_float(base_recipe[field])
                
        # Handle Empty Strings -> None (for all other fields)
        for k, v in base_recipe.items():
            if v == "":
                base_recipe[k] = None
                
        # --- Standardization End ---

        # 4. Content Specifics (Linux vs Dragon) handling is implicit 
        # because form_data should already contain the keys.
        
        new_experiments = []
        test_type = form_data.get('Test Type')
        test_name = form_data.get('Test Name')
        start = form_data.get('Start') # Original values for loop usage
        end = form_data.get('End')
        steps = form_data.get('Steps')
        sweep_dom = form_data.get('Sweep Domain')
        
        # 5. Sweep / Shmoo Generation
        if test_type in ["Sweep", "Shmoo"]:
            try:
                val_start = float(start)
                val_end = float(end)
                val_step = float(steps)
                if val_step == 0: val_step = 0.01
                
                sweep_values = np.arange(val_start, val_end + (val_step/2), val_step)
                
                for i, val in enumerate(sweep_values):
                    val_formatted = f"{val:.3f}" # Keep string format for Name construction
                    val_float = float(val_formatted) # Float for value injection
                    
                    step_name = f"{test_name}_{sweep_dom}_{val_formatted}"
                    
                    step_recipe = base_recipe.copy()
                    
                    # Override the specific sweep value with the float
                    if sweep_dom == "IA": step_recipe["Voltage IA"] = val_float
                    elif sweep_dom == "CFC": step_recipe["Voltage CFC"] = val_float
                    elif "VVAR" in sweep_dom: step_recipe[sweep_dom] = val_formatted # VVARs might be strings (hex) or ints? Examples show Hex String.
                    
                    new_experiments.append({
                        "Experiment": step_name,
                        "Category": "Sweep",
                        "SubCategory": sweep_dom,
                        "Estado": "Pending",
                        "FailRate": 0,
                        "Template": form_data.get('Scripts File'),
                        "Content": form_data.get('Content'),
                        "Test Mode": test_mode,
                        "Test Type": test_type,
                        "RecipeData": step_recipe
                    })
            except Exception as e:
                return False, f"Error generating sweep: {str(e)}", 0
        else:
            # Single Experiment
            new_experiments.append({
                "Experiment": test_name,
                "Category": "FrameworkV2",
                "SubCategory": test_type,
                "Estado": "Pending",
                "FailRate": 0,
                "Template": form_data.get('Scripts File'),
                "Content": form_data.get('Content'),
                "Test Mode": test_mode,
                "Test Type": test_type,
                "RecipeData": base_recipe
            })

        # 6. Save / Update Logic
        existing_experiments = unit_json.get('experiments', [])
        
        # Check if we are updating a single existing experiment (by name)
        # Note: Sweeps generate multiple names, so they usually just append or overwrite specific steps.
        # The logic in dashboard was: if test_name exists, update it.
        # But for sweeps, test_name is the prefix.
        
        msg = ""
        if test_type not in ["Sweep", "Shmoo"]:
            # Single Update
            existing_idx = next((i for i, e in enumerate(existing_experiments) if e.get("Experiment") == test_name), -1)
            
            if existing_idx >= 0:
                # Update existing
                existing_experiments[existing_idx].update(new_experiments[0])
                msg = f"Experiment '{test_name}' updated."
            else:
                # Append new
                existing_experiments.extend(new_experiments)
                msg = "Experiment Created."
        else:
            # Sweep: Always Append for now (as per original logic roughly)
            # Or should we check for existing steps? 
            # Original logic: if existing_idx >= 0 -> Update. But Step names are different from 'Test Name'.
            # Original logic lines 369: checked `e.get("Experiment") == test_name`.
            # For sweeps, the experiment name is `test_name_domain_val`.
            # So `test_name` itself won't match any experiment name.
            # Thus, sweeps were always being "extended" (Added).
            existing_experiments.extend(new_experiments)
            msg = f"{len(new_experiments)} Sweep Steps Created."

        # 7. Persist
        to_save = unit_json.copy()
        if '_context' in to_save: del to_save['_context']
        
        success, save_msg = DataHandler.save_unit_data(product, bucket, unit, to_save, platform)
        
        if success:
            return True, msg, int(time.time())
        else:
            return False, save_msg, 0
            
    @staticmethod
    def delete_experiments(product, bucket, unit, exp_names, platform='AP'):
        data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
        if not data: return False, msg
        
        original_count = len(data.get("experiments", []))
        data["experiments"] = [e for e in data.get("experiments", []) if e.get("Experiment") not in exp_names]
        
        if len(data["experiments"]) == original_count:
            return False, "No experiments found to delete"
            
        return DataHandler.save_unit_data(product, bucket, unit, data, platform)

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

    @staticmethod
    def activate_experiments(product, bucket, unit, exp_names, platform='AP'):
        data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
        if not data: return False, msg
        
        selected_exps = [e for e in data.get("experiments", []) if e.get("Experiment") in exp_names]
        pending_exps = [e for e in selected_exps if e.get("Estado") == "Pending"]
        
        if not pending_exps:
            return False, "No 'Pending' experiments selected"
            
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        date_str = now.strftime("%Y%m%d")
        
        recipe_dict = {}
        step_idx = 1
        
        # Grouping for Sweeps
        sweep_groups = {} 
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
            base_rd = group[0].get("RecipeData", {}).copy()
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
        import os
        import json
        
        # We need the path to save the recipe. DataHandler has the logic to construct path.
        # But DataHandler.get_unit_path is private-ish? No, likely static.
        # Let's assume we can construct it or expose it.
        # Actually, let's look at how DataHandler does it. It constructs path from config.PRODUCTS_DIR.
        from config import PRODUCTS_DIR
        unit_dir = os.path.join(PRODUCTS_DIR, product, 'Buckets', bucket, 'Results_Data', 'Units', platform, unit)
        
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
                    
            return DataHandler.save_unit_data(product, bucket, unit, data, platform)
        except Exception as e:
            return False, f"Error saving recipe: {str(e)}"

    @staticmethod
    def update_experiments(product, bucket, unit, experiments, platform='AP'):
        data, msg = DataHandler.load_unit_data(product, bucket, unit, platform)
        if not data: return False, msg
        
        data['experiments'] = experiments
        return DataHandler.save_unit_data(product, bucket, unit, data, platform)
