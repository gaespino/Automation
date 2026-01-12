import os
import json
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog


class JsonReader:
    def __init__(self, logger: ILog, file_path: str, json_data: dict=None):
        self._logger = logger
        self._file_path = file_path
        self._json_data = json_data
        self._read_file_data()

    def _read_file_data(self):
        script_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = rf"{script_folder}/src/gui/{self._file_path}"
        if not os.path.isfile(full_path):
            raise FileNotFoundError
        with open(full_path, 'r') as file:
            try:
                self._json_data = json.load(file)
            except Exception as e:
                raise e


    def get_json_data(self):
        if self._json_data is None:
            self._read_file_data()
        return self._json_data

    def get(self, key:str):
        return self._json_data.get(key, {})
