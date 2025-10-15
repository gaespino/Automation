def validate_field(value, field_info):
    str_value = value.get().strip()
    if field_info["required"] and not value:
        return False, f"{field_info['name']} is required"

    if field_info["type"] == "float":
        try:
            float(value)
        except ValueError:
            return False, f"{field_info['name']} must be a float"

    return True, ""
