import json
import itertools
import os


def read_json_file(file_path):
    """
    Reads a JSON file and returns its content as a dictionary.
    
    Parameters:
    file_path (str): The path to the JSON file.
    
    Returns:
    dict: The content of the JSON file as a dictionary, or None if an error occurs.
    """
    try:
        # Attempt to open and read the JSON file
        with open(file_path, "r") as file:
            dictionary = json.load(file)
        return dictionary

    except FileNotFoundError:
        # Handle the error if the file is not found
        print(f"Error: The json file '{file_path}' was not found.")
        return None

    except json.JSONDecodeError:
        # Handle the error if the file content is not valid JSON
        print(f"Error: The file '{file_path}' does not contain valid JSON.")
        return None

    except Exception as e:
        # Handle any other type of error
        print(f"An unexpected error occurred: {e}")
        return None


def generate_fuses(key, filter_params={}):
    """
    Generate fuses based on the provided key and optional filter parameters.

    :param key: The key to look up in the JSON data.
    :param filter_params: A dictionary where keys are parameter names and values are lists of values to filter by.
                          If empty, no filtering is applied.
    :return: A list of generated fuses.
    """
    # Read JSON with fuses information
    current_dir = os.path.dirname(__file__)
    json_filename = "recipe_data.json"
    json_path = os.path.join(current_dir, json_filename)
    json_data = read_json_file(json_path)

    # Get the dataset corresponding to the provided key
    dynamic_injection = json_data["dynamic_injections"].get(key)
    if not dynamic_injection:
        return []

    # Get sockets and fuses
    sockets = dynamic_injection["sockets"]
    fuses_list = dynamic_injection["fuses"]

    all_fuses = []

    # Iterate over each dictionary in the fuses list
    for fuse in fuses_list:
        template = fuse["template"]
        parameters = fuse["parameters"]

        # Generate all possible combinations of parameters
        keys = list(parameters.keys())
        combinations = itertools.product(*(parameters[key] for key in keys))

        # If filter_params is not empty, filter combinations based on filter_params
        if filter_params:
            combinations = [
                combination for combination in combinations
                if all(value in filter_params.get(key, parameters[key]) for key, value in zip(keys, combination))
            ]

        # For each combination, generate the fuse
        for combination in combinations:
            fuse_string = template
            for key, value in zip(keys, combination):
                fuse_string = fuse_string.replace(f"&{key}&", value)

            # Precede each fuse with "sv." followed by the socket name
            for socket in sockets:
                all_fuses.append(f"sv.{socket}.{fuse_string}")

    return all_fuses
    


def generate_fuses_no_filtered(key):
    # Read json with fuses information
    current_dir = os.path.dirname(__file__)
    json_filename = "recipe_data.json"
    json_path = os.path.join(current_dir, json_filename)
    json_data = read_json_file(json_path)

    # Obtener el conjunto de datos correspondiente al key proporcionado
    dynamic_injection = json_data["dynamic_injections"].get(key)
    if not dynamic_injection:
        return []

    # Obtener los sockets y fuses
    sockets = dynamic_injection["sockets"]
    fuses_list = dynamic_injection["fuses"]

    all_fuses = []

    # Iterar sobre cada diccionario en la lista de fuses
    for fuse in fuses_list:
        template = fuse["template"]
        parameters = fuse["parameters"]

        # Generar todas las combinaciones posibles de parámetros
        keys = list(parameters.keys())
        combinations = itertools.product(*(parameters[key] for key in keys))

        # Para cada combinación, generar el fuse
        for combination in combinations:
            fuse_string = template
            for key, value in zip(keys, combination):
                fuse_string = fuse_string.replace(f"&{key}&", value)

            # Preceder cada fuse con "sv." seguido del nombre del socket
            for socket in sockets:
                all_fuses.append(f"sv.{socket}.{fuse_string}")

    return all_fuses




if __name__ == "__main__":
    #json_path = "recipe_data.json"
    #json_path = ".\test.json"
    #json_data = read_json_file(json_path)

    #print(json_data)

    import os
    #print(os.path.exists(json_path))
    print(os.getcwd())

    filter_params = {
        "dies": ["cbb0"],
        "cores": ["core0"]
    }
    filter_params = None

    # Generar fuses para el key "cfc_voltage_bump"
    fuses = generate_fuses("cfc_voltage_bump", filter_params=filter_params)

    #from pprint import pprint
    #pprint(fuses)