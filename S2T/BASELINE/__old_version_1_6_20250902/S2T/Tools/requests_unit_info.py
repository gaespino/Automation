from datetime import datetime
from tabulate import tabulate
import pandas as pd
import time
import uuid
import json
import os
import sys

REQUEST_FOLDER = r"\\amr.corp.intel.com\ec\proj\mdl\cr\prod\hdmx_intel\engineering\dev\team_thr\zamora3\unit_info_utility\requests"
RESPONSE_FOLDER = r"\\amr.corp.intel.com\ec\proj\mdl\cr\prod\hdmx_intel\engineering\dev\team_thr\zamora3\unit_info_utility\responses"

class UnitInfo:
    def __init__(self, sv=None, ipc=None, ult=None, visual=None):
        self._ult = ult
        self._sv = sv
        self._ipc = ipc
        self._visual = visual
        self._set_ult()

    def _set_ult(self):
        if self._ult is None and self._visual is None:
            import graniterapids.toolext.bootscript.toolbox.ult_module as _ult
            from ipccli.bitdata import BitData as _BitData
            ult_in = self._sv.socket0.compute0.fuses.dfxagg_top.ult_fuse
            if int(ult_in) == 0:
                self._sv.socket0.compute0.fuses.load_fuse_ram()
                ult_in = self._sv.socket0.compute0.fuses.dfxagg_top.ult_fuse
            ult_str = _ult.ult(_BitData(64, 0) | ult_in)
            self._ult = ult_str

    def send_request(self):
        os.makedirs(REQUEST_FOLDER, exist_ok=True)
        request_id = str(uuid.uuid4())
        request_data = {
            "id": request_id,
            "ult": self._ult,
            "visual": self._visual,
            "timestamp": datetime.now().isoformat()
        }
        request_file = os.path.join(REQUEST_FOLDER, f"{request_id}.json")
        with open(request_file, "w") as f:
            json.dump(request_data, f)
        print(f"Unit data Request {request_id} sent.")
        return request_id

    def check_response(self, request_id):
        response_file = os.path.join(RESPONSE_FOLDER, f"{request_id}.csv")
        if os.path.exists(response_file):
            print("\nResponse ready:")
            df = pd.read_csv(response_file)
            print(tabulate(df, headers='keys', tablefmt='grid'))
            return df.to_dict()
        else:
            return None

def print_retry_progress(current_attempt, total_attempts, elapsed_time, length=30):
    """Print retry progress bar showing attempts and time"""
    filled_length = int(length * current_attempt // total_attempts)
    bar = '+' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r[{bar}] Attempt {current_attempt}/{total_attempts} | {elapsed_time}s elapsed')
    sys.stdout.flush()

def get_unit_info(sv=None, ipc=None, ult=None):
    unit = UnitInfo(sv=sv, ipc=ipc, ult=ult)
    request_id = unit.send_request()
    response_data = None
    
    max_attempts = 150
    print(f"Waiting for response (Request ID: {request_id}...):")
    
    for i in range(max_attempts):
        current_attempt = i + 1
        elapsed_time = current_attempt * 5
        
        response_data = unit.check_response(request_id)
        if response_data:
            print_retry_progress(max_attempts, max_attempts, elapsed_time)  # Complete the bar
            print(f"\n✓ Response received on attempt {current_attempt}/{max_attempts} after {elapsed_time}s!")
            break
        
        print_retry_progress(current_attempt, max_attempts, elapsed_time)
        time.sleep(5)
    
    if not response_data:
        print(f"\n✗ No response after {max_attempts} attempts ({max_attempts * 5}s total)")
    
    return response_data