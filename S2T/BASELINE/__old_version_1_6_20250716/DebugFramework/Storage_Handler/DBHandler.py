
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import DBClient as DB_Client
import ReportUtils as reportUtils 


pqe_mongo_db_credentials = __import__('MongoDBCredentials', globals(), locals(), [], 0)
DANTA_DB_PASSWORD = os.environ.get('DANTA_DB_PASSWORD', None)
CONNECTION_STRING = pqe_mongo_db_credentials.DANTA_DB_CREDENTIAL.format(DANTA_DB_PASSWORD)



collection_name_mapping={
   "CHA":"SYSTEM_DEBUG_FRAMEWORK_RVP_CHA_DATA_COLLECTION",
   "CORE":"SYSTEM_DEBUG_FRAMEWORK_RVP_CORE_DATA_COLLECTION",
   "PPV":"SYSTEM_DEBUG_FRAMEWORK_RVP_PPV_DATA_COLLECTION",
   "CHA_MCAS":"SYSTEM_DEBUG_FRAMEWORK_RVP_CHA_MCAS_DATA_COLLECTION",
   "LLC_MCAS":"SYSTEM_DEBUG_FRAMEWORK_RVP_LLC_MCAS_DATA_COLLECTION",
   "UBOX":"SYSTEM_DEBUG_FRAMEWORK_RVP_UBOX_DATA_COLLECTION",
   "CORE_MCAS":"SYSTEM_DEBUG_FRAMEWORK_RVP_CORE_MCAS_DATA_COLLECTION"
}

def upload_summary_report_batch(experiment_output):
    file_results=reportUtils.find_excel_files(experiment_output)
    for current_result in file_results:
        upload_summary_report(current_result)



def upload_summary_report(storage_dir):
    try:
        file_path=reportUtils.find_excel_files(storage_dir)[0]
    except:
        sys.exit(f"Error: Summary file not found in directory '{storage_dir}'")

    
    summary_data_dict,visual_id=reportUtils.create_reduced_object_excel_representation(file_path=file_path)

    #Get DB Interface 
    DB_client=DB_Client.DB_Client(CONNECTION_STRING)

    #Get Experiment Name
    experiment_key=os.path.basename(storage_dir)

    #Get ID
    id=reportUtils.generate_ID(visual_id,experiment_key)

    for report_name in summary_data_dict:
        collection_name=collection_name_mapping[report_name]
        report_content=summary_data_dict[report_name]
        db_entry={
            "_id":id,
            "data":json.dumps(report_content), #Formating the object to string to meet the database guidelines
            "storage":storage_dir,
            "visual_id":visual_id,
            "date-last-updated":reportUtils.get_mongo_database_date_format()
        }

        DB_client.add_item(collection_name=collection_name,item=db_entry)
        
def create_storage_collections():

    #Create DB Client
    DB_client=DB_Client(CONNECTION_STRING)

    #iterate through collection
    for collection in collection_name_mapping:
        DB_client.create_collection(collection_name_mapping[collection])

  


def test():
    file_path=r"I:\engineering\dev\user_links\gaespino\DebugFramework\GNR\75MA888700252\cr03tppv0164en\20250630\20250630_084450_T1_BaselineChecks-VoltageSweeps_UMA_Sweep"
    upload_summary_report(file_path)

if __name__ == "__main__":
    test()


