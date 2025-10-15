import os
import json
import time
from datetime import datetime


REQUEST_FOLDER = r"\\amr.corp.intel.com\ec\proj\mdl\cr\prod\hdmx_intel\engineering\dev\team_thr\zamora3\unit_info_utility\requests"
RESPONSE_FOLDER = r"\\amr.corp.intel.com\ec\proj\mdl\cr\prod\hdmx_intel\engineering\dev\team_thr\zamora3\unit_info_utility\responses"


def process_request(request_file):
    with open(request_file, "r") as f:
        request_data = json.load(f)

    # Aquí generas el reporte según los parámetros
    report = {
        "report": f"Processed request {request_data['id']}",
        "parameters": request_data["parameters"],
        "processed_at": datetime.now().isoformat()
    }

    # Guardar respuesta
    os.makedirs(RESPONSE_FOLDER, exist_ok=True)
    response_file = os.path.join(RESPONSE_FOLDER, f"{request_data['id']}.json")
    with open(response_file, "w") as f:
        json.dump(report, f)

    print(f"Processed request {request_data['id']}")


def consume_requests():
    execute_process = True
    while execute_process:
        try:
            request_files = [f for f in os.listdir(REQUEST_FOLDER) if f.endswith(".json")]
            for req_file in request_files:
                full_path = os.path.join(REQUEST_FOLDER, req_file)
                process_request(full_path)
                #os.remove(full_path)
        except Exception as e:
            execute_process = False
        time.sleep(5)


if __name__ == "__main__":
    consume_requests()