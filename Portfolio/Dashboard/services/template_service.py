import os
import json
import time

# Assuming config is available. If not, use relative imports or path construction.
from config import BASE_DIR

TEMPLATES_DIR = os.path.join(BASE_DIR, 'settings', 'templates')

class TemplateService:
    
    @staticmethod
    def ensure_template_dir():
        if not os.path.exists(TEMPLATES_DIR):
            os.makedirs(TEMPLATES_DIR)

    @staticmethod
    def save_template(name, experiments):
        """
        Saves a list of experiment dicts as a template JSON.
        """
        if not name:
            return False, "Template name is required"
        if not experiments:
            return False, "No experiments to save"
            
        TemplateService.ensure_template_dir()
        
        # Sanitize filename
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
        file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(experiments, f, indent=4)
            return True, f"Recipe '{name}' saved successfully."
        except Exception as e:
            return False, f"Error saving template: {str(e)}"

    @staticmethod
    def get_templates():
        """
        Returns a list of available template names.
        """
        TemplateService.ensure_template_dir()
        try:
            files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.json')]
            return [os.path.splitext(f)[0] for f in files]
        except Exception:
            return []

    @staticmethod
    def load_template(name):
        """
        Loads a template by name. Returns list of experiments or None.
        """
        TemplateService.ensure_template_dir()
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
        file_path = os.path.join(TEMPLATES_DIR, f"{safe_name}.json")
        
        if not os.path.exists(file_path):
            return None, "Template not found"
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data, "Loaded"
        except Exception as e:
            return None, f"Error loading template: {str(e)}"

    @staticmethod
    def apply_template_to_unit(unit_data, template_experiments):
        """
        Adds template experiments to unit data with unique naming.
        """
        if not unit_data or not template_experiments:
            return False, "Invalid data"

        current_exps = unit_data.get('experiments', [])
        added_count = 0
        
        for tmpl_exp in template_experiments:
            # Create a copy to avoid reference issues
            new_exp = tmpl_exp.copy()
            
            # Reset Status
            new_exp["Estado"] = "Pending"
            new_exp["FailRate"] = 0
            new_exp["Link"] = "" # Clear previous links if any
            
            # Generate Unique Name
            original_name = new_exp.get("Experiment", "Exp")
            base_name = original_name
            # If name already has a timestamp or copy suffix, maybe strip it? 
            # User wants to reuse workflow, so likely keeps name.
            
            idx = 1
            final_name = base_name
            
            # Check collision in current unit AND in the batch being added
            while any(e.get("Experiment") == final_name for e in current_exps):
                final_name = f"{base_name}_{idx}"
                idx += 1
            
            new_exp["Experiment"] = final_name
            
            current_exps.append(new_exp)
            added_count += 1
            
        unit_data['experiments'] = current_exps
        return True, f"{added_count} experiments added from recipe."
