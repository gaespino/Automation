from datetime import datetime
from tabulate import tabulate
import pandas as pd
import time
import uuid
import json
import os


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
        print(f"Request {request_id} sent.")
        return request_id

    def check_response(self, request_id):
        response_file = os.path.join(RESPONSE_FOLDER, f"{request_id}.csv")
        if os.path.exists(response_file):
            print("Response ready:")
            df = pd.read_csv(response_file)
            print(tabulate(df, headers='keys', tablefmt='grid'))
            return df.to_dict()
        else:
            print("Response not ready yet.")
            return None

def get_unit_info(sv=None, ipc=None, ult=None):
    unit = UnitInfo(sv=sv, ipc=ipc, ult=ult)
    request_id = unit.send_request()
    response_data = None
    for i in range(0, 150):
        response_data = unit.check_response(request_id)
        if response_data:
            break
        time.sleep(5)
    return response_data

