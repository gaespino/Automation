
try:
    from users.gaespino.dev.DebugFramework.Storage_Handler.DBClient import DB_Client
    import users.gaespino.dev.DebugFramework.Storage_Handler.ReportUtils as reportUtils
    import users.gaespino.dev.DebugFramework.Storage_Handler.MongoDBCredentials as pqe_mongo_db_credentials
    
except:
    print('import failed: Trying a different source')
    from DBClient import DB_Client
    import ReportUtils as reportUtils
    import MongoDBCredentials as pqe_mongo_db_credentials

import json
import os





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

def decode_path(storage_dir):
    #Split file path to extract experiment info
    splitted_path = os.path.normpath(storage_dir).lstrip("\\/").split(os.sep)
    print(f"Splitted path is {splitted_path}")
    #Get Experiment Info
    experiment_key=splitted_path[-1]
    date=splitted_path[-2]
    host=splitted_path[-3]
    visual_id=splitted_path[-4]
    product=splitted_path[-5]
    return experiment_key,date,host,visual_id,product

def upload_summary_report_batch(local_copy_dir):

    file_results=reportUtils.find_excel_files(local_copy_dir)
    for current_result in file_results:
        upload_summary_report(os.path.dirname(current_result))



def upload_summary_report(storage_dir,logger=None):
    
    #Setting logger to print if not provided
    if logger == None: logger = print
    logger(f"Logging Summary from {storage_dir} to Database")

    try:
        file_path=reportUtils.find_excel_files(storage_dir)[0]
    except:
        logger(f"Error: Summary file not found in directory '{storage_dir}'")

    
    summary_data_dict=reportUtils.create_reduced_object_excel_representation(file_path=file_path)

    #Get DB Interface 
    DB_client=DB_Client(CONNECTION_STRING,logger=logger)

    #Get Decoded Field
    experiment_key,date,host,visual_id,product=decode_path(storage_dir)

    #SET ID
    id=f"{product}_{visual_id}_{host}_{date}_{experiment_key}"

    for report_name in summary_data_dict:
        collection_name=collection_name_mapping[report_name]
        report_content=summary_data_dict[report_name]
        db_entry={
            "_id":id,
            "data":json.dumps(report_content), #Formating the object to string to meet the database guidelines
            "storage":storage_dir,
            "visual_id":visual_id,
            "product":product,
            "date-last-updated":reportUtils.get_mongo_database_date_format()
        }

        DB_client.add_item(collection_name=collection_name,item=db_entry)


def delete_summary_report(storage_dir,logger=None):
    
    #Setting logger to print if not provided
    if logger == None: logger = print
    logger(f"Logging Summary from {storage_dir} to Database")

    #Get DB Interface 
    DB_client=DB_Client(CONNECTION_STRING,logger=logger)

    #Get Decoded Field
    experiment_key,date,host,visual_id,product=decode_path(storage_dir)

    #SET ID
    id=f"{product}_{visual_id}_{host}_{date}_{experiment_key}"

    for collection_name in collection_name_mapping.values():
        DB_client.delete_item(
            collection_name=collection_name,
            query={
                "_id":id
            }
        )

def move_summary_report(original_storage_dir,new_storage_dir,logger=None):
    delete_summary_report(original_storage_dir,logger)
    upload_summary_report(new_storage_dir,logger)

def upload_summary_report_dupe(storage_dir,logger=None):
    delete_summary_report(storage_dir,logger)
    upload_summary_report(storage_dir,logger=None)



        
def create_storage_collections():

    #Create DB Client
    DB_client=DB_Client(CONNECTION_STRING)

    #iterate through collection
    for collection in collection_name_mapping:
        DB_client.create_collection(collection_name_mapping[collection])

def delete_storage_collections():

    #Create DB Client
    DB_client=DB_Client(CONNECTION_STRING)

    #iterate through collection
    for collection in collection_name_mapping:
        DB_client.delete_collection(collection_name_mapping[collection])




def test_batch():
    delete_storage_collections()
    create_storage_collections()
    #file_path=r"I:\engineering\dev\user_links\gaespino\DebugFramework\GNR\75MA888700252\cr03tppv0164en\20250630\20250630_084450_T1_BaselineChecks-VoltageSweeps_UMA_Sweep"
    #upload_summary_report(file_path)
    local_dir=r"\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework"
    upload_summary_report_batch(local_dir)

def test():
    file_path=r"\\Amr\ec\proj\mdl\cr\intel\engineering\dev\user_links\gaespino\DebugFramework\GNR\75VP061900080\cr03tppv0162en\20250716\20250715_205315_T4_CFC_Voltage_check_Sweep"
    upload_summary_report(file_path)



if __name__ == "__main__":
    test()
    #test_batch()




