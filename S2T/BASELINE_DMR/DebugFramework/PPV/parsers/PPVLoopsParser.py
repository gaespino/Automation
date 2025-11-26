import os
import zipfile
import re
import pandas as pd
import shutil
import argparse

debug = True

def argparser(debug):
	if not debug:
		parser = argparse.ArgumentParser()
		typehelp = ("Shmoo configuration for GNR Tester")

		# Add Argument list below
		parser.add_argument('-folder', type=str, required= True,
							help = "Content Shmoos to be enabled")
		parser.add_argument('-output', type=str, required= True,
							help = "Content Shmoos to be enabled")
		parser.add_argument('-key',  default=100 ,type=int, required= False,
							help = "Content Shmoos to be enabled")
		parser.add_argument('-bucket', default='N/A', required= False,
							help = "Enable / Disable option for shmoo config ")
		parser.add_argument('-WW', type=str, default='N/A', required= False,
							help = "Name of the shmoo to be used from UNCORE SHMOO FILE")
		parser.add_argument('-zfile', type=bool, default=False, required= False,
							help = "Masking file to change FCTRACKING A, B, C or D")

		args = parser.parse_args()
	
	# Default arguments for debug mode of the script
	else:
		class Args:
			#savefile = 'I:\\intel\\engineering\\dev\\team_ftw\\gaespino\\EMRMCC\\PEGA_SHMOOS_VF_NOVF\\ShmooParsed_Data.txt'
			folder = r'Q:/DPM_Debug/GNR/Logs/IDI/02_March_74B95D0700360/PTC/'
			output = r'C:\ParsingFiles\PPV_Loops_Parser\core_idi_UnitData.xlsx'
			key = 100
			bucket = 'CORE_IDI'
			WW = 'WW11'
			zfile = False

		args = Args()
	
	return args

class LogsPTC():

    def __init__(self, StartWW, bucket, LotsSeqKey, folder_path, output_file, zipfile=False, dpmbformat=True):
        self.dpmb_Cols = ['VisualId','Lot','LatoStartWW','LotsSeqKey','UnitTestingSeqKey','TestName','TestValue','Operation','TestNameNumber','TestNameWithoutNumeric']
        self.ppv_Cols = ['VisualId','DpmBucket','DecimaSite','DecimaWW','DecimaBucket','DpmBucketAccuracy','ProductConfigurationName']
        self.results_Cols = ['VisualId','BinDesc']
        self.bucketSheet  ='final_bucket'
        self.dpmbdata = {'VisualId':[],'Lot':[],'LatoStartWW':[],'LotsSeqKey':[],'UnitTestingSeqKey':[],'TestName':[],'TestValue':[],'Operation':[],'TestNameNumber':[],'TestNameWithoutNumeric':[], 'QDF':[],'ValueType': []}
        self.ppvdata = {'VisualId':[],'DpmBucket':[],'DecimaSite':[],'DecimaWW':[],'DecimaBucket':[],'DpmBucketAccuracy':[],'ProductConfigurationName':[],'BinDesc':[]}
        self.folder_path = folder_path #r'Q:\ddcanale\PTC Logs\TORTO\745N5S5800396\01_nominal_Fail_Sequencer 2'
        self.output_file = output_file #r'Q:\ddcanale\PTC Logs\TORTO\745N5S5800396\01_745N5S5800396.xlsx'
        self.zipfile = zipfile

        ## Data for RAW Tab
        self.files = {}
        self.data = 'raw_data'
        self.search_string = 'Logging test to iTUFF for socket all:'
        
        self.unitstart = 'Unit start requested for handler unit ID'
        self.LatoStartWW = StartWW
        self.LotsSeqKey = LotsSeqKey
        self.UnitTestingSeqKey = 0

        ## This switch is for Debug purposes, will look for Logging registers instead of the ituff data
        self.dpmbformat = dpmbformat
        self.search_string_ptc = 'Logging register:'
        # Data for Results & Final_bucket
        self.resultsSheet = 'results'
        self.finalSheet = 'final_bucket'
        self.bin_string = 'Final Bin = '
        self.binfiles = {}
        self.resultsfiles = {}
        self.DpmBucket = bucket
        self.DecimaSite = 'CR'
        self.DecimaWW = StartWW
        self.DecimaBucket = ' '
        self.DpmBucketAccuracy = ' '
        self.ProductConfigurationName = ' '
        self.BinDesc = ' '

        ## DPMB Variables init
        self.dpmb_location = ''
        self.dpmb_qdf  = ''
        self.dpmb_lot = ''
        self.dpmb_vid = '-99999999999'
        self.dpmb_step = ''
        self.dpmb_program = ''


    def run(self):
        folder_path = self.folder_path
        search_string = self.search_string
        seqRuns = self.files
        final_bucket = self.binfiles
        results = self.resultsfiles

        print(f'MSG-- Looking for PPV files in folder {folder_path}-- Process will take a few minutes, please wait.')
        if self.zipfile: self.search_in_folder(folder_path, search_string)
        else: self.search_in_directory(folder_path, search_string)

        datalog = pd.concat(seqRuns.values(), ignore_index=True)
        binlog = pd.concat(final_bucket.values(), ignore_index=True)
        resultslog = pd.concat(results.values(), ignore_index=True)

        logs = datalog[self.dpmb_Cols]
        
        print(f'MSG-- Saving data in excel file at location: {self.output_file}.')
        with pd.ExcelWriter(self.output_file) as writer:   
            resultslog.to_excel(writer, sheet_name=self.resultsSheet, index=False)
            logs.to_excel(writer, sheet_name=self.data, index=False)
            binlog.to_excel(writer, sheet_name=self.finalSheet, index=False)
            #mc_df.to_excel(writer, sheet_name='mc_data', index=False)
        print(f'MSG-- Parse complete.')

    def parse_line(self, line):
        match = re.search(r'\[(.*?)\]', line)
        if match:
            return match.group(1).split(',')
        return None

    def parse_logging(self, line):
        match = re.search('with value:', line)
        if match:
            nline = line.split(' ')
            data = [nline[5], nline[-1], 'str']
            return data
        return None

    def search_in_file(self, file_path, search_string, zip_path, debuglog, seq):
        folder = os.path.dirname(file_path).split('\\')[-1]
        env = ['Location Code:', 'SSPEC:','Lot Name:']



        # Variable Declaration   
        dpmb_data = []
        dpmb_location = ''
        dpmb_qdf  = ''
        dpmb_lot = ''
        dpmb_vid = '-99999999999'
        dpmb_step = ''
        dpmb_program = ''
        dpmb_sequence = seq

        if self.infolder: # This variable comes from previous directory check
            dpmb_location = ''
            dpmb_qdf  = ''
            dpmb_lot = ''
            dpmb_vid = '-99999999999'
            dpmb_step = ''
            dpmb_program = ''

        else:
            dpmb_location = ''
            dpmb_qdf  = ''
            dpmb_lot = ''
            dpmb_vid = '-99999999999'
            dpmb_step = ''
            dpmb_program = ''
     
        # Data dictionary build
        data =      {
                        'VisualId'                  :[],
                        'Lot'                       :[],
                        'LatoStartWW'               :[],
                        'LotsSeqKey'                :[],
                        'UnitTestingSeqKey'         :[],
                        'TestName'                  :[],
                        'TestValue'                 :[],
                        'Operation'                 :[],
                        'TestNameNumber'            :[],
                        'TestNameWithoutNumeric'    :[], 
                        'QDF'                       :[],
                        'ValueType'                 :[]
                    }
     
        results = {
                        'VisualId'                  :[],
                        'Lot'                       :[],
                        'LatoStartWW'               :[self.LatoStartWW],
                        'LotsSeqKey'                :[self.LotsSeqKey],
                        'UnitTestingSeqKey'         :[dpmb_sequence],
                        'DpmBucket'                 :[self.DpmBucket],
                        'DecimaSite'                :[self.DecimaSite],
                        'DecimaWW'                  :[self.DecimaWW],
                        'DecimaBucket'              :[self.DecimaBucket],
                        'Accuracy'                  :[self.DpmBucketAccuracy],
                        'Operation'                 :[],
                        'ProductConfigurationName'  :[self.ProductConfigurationName],
                        'Program'                   :[],
                        'SSPEC'                     :[],
                        'DevRevStep'                :[],
                        'TestName'                  :[],                        
                        'TestValue'                 :[],                     
                        'DB'                        :[],   
                        'BinDesc'                   :[],   
                    }
        
        final_bin = {   
                        'VisualId'                  :[],
                        'DpmBucket'                 :[self.DpmBucket],
                        'DecimaSite'                :[self.DecimaSite],
                        'DecimaWW'                  :[self.DecimaWW],
                        'DecimaBucket'              :[self.DecimaBucket],
                        'DpmBucketAccuracy'         :[self.DpmBucketAccuracy],
                        'ProductConfigurationName'  :[self.ProductConfigurationName]}
        

        # Open file to start searching for strings
        with open(file_path, 'r') as file:
            lines = file.readlines()

            for line in lines:
                #if any(e in line for e in env_data.keys()):
                
                if 'Location Code:' in line and data['Operation'] != None:
                    dpmb_location = line.split(":")[1].strip() # Looks for this string and returns
               
                if 'SSPEC:' in line and data['QDF'] != None:
                    dpmb_qdf = line.split(":")[1].strip() # Looks for this string and returns
                
                if 'Lot Name:' in line and data['Lot'] != None:
                    dpmb_lot = line.split(":")[1].strip() # Looks for this string and returns
                
                if 'Current Visual VID' in line:
                    dpmb_vid = line.split(" ")[-1].strip() # Looks at the position for the desired Text

                parsed_line = self.parse_line(line)
                ptcstring = self.search_string_ptc
                notlogging = self.dpmbformat
                if search_string in line and parsed_line is not None and notlogging:
                    #dpmb_data = [zip_path.rstrip('.zip')] + [folder] + parse_line(line) for line in lines if search_string in line and parse_line(line) is not None]
                    if 'dpmbucketer_socket0' in line or 'dpmb_socket0' in line:                 
                        dpmb_data += [parsed_line]
                        #data['TestName'] += dpmb_data[0].upper()
                        #data['TestValue'] += dpmb_data[1].upper()
                        #data['ValueType'] += dpmb_data[2]
                
                if ptcstring in line and not notlogging:
                    parsed_log = self.parse_logging(line)
                    if  parsed_log:
                        #  if 'Logging register:' in line:
                        dpmb_data +=[parsed_log]
        
        if self.infolder: # This variable comes from previous directory check
            self.dpmb_location = dpmb_location if dpmb_location != '' else self.dpmb_location #''
            self.dpmb_qdf  = dpmb_qdf if dpmb_qdf != '' else self.dpmb_qdf #''
            self.dpmb_lot = dpmb_lot if dpmb_lot != '' else self.dpmb_lot #''
            self.dpmb_vid = dpmb_vid if dpmb_vid != '' else self.dpmb_vid #'-99999999999'
            self.dpmb_step = dpmb_step if dpmb_step != '' else self.dpmb_step #''
            self.dpmb_program = dpmb_program if dpmb_program != '' else self.dpmb_program #''



        # Build the Raw Data info for the sequence 
        for d in dpmb_data:
            data['TestName'] += [f'{d[0].upper()}_{self.dpmb_location}']
            data['TestValue'] += [d[1].upper()]
            data['ValueType'] += [d[2]]
        
        data['TestNameWithoutNumeric'] = data['TestName']

        # Fill Data in the other raw data dict keys to be the same size as the MCA data collected
        for l in range(len(data['TestName'])):
            #self.dpmbdata = {'VisualId':[],'Lot':[],'LatoStartWW':[],'LotsSeqKey':[],'UnitTestingSeqKey':[],'TestName':[],'TestValue':[],'Operation':[],'TestNameNumber':[],'TestNameWithoutNumeric':[], 'QDF':[],'ValueType': []}
            data['VisualId'] += [dpmb_vid]
            data['Operation'] += [dpmb_location]
            data['Lot'] += [dpmb_lot]
            data['QDF'] += [dpmb_qdf]
            data['LatoStartWW'] += [self.LatoStartWW]
            data['LotsSeqKey'] += [self.LotsSeqKey]
            data['UnitTestingSeqKey'] += [f'{dpmb_sequence}']
            data['TestNameNumber'] += ['0']
        
        # Fill Results Dictionary missing keys
        results['VisualId'] = [self.dpmb_vid]
        results['Lot'] = [self.dpmb_lot]
        results['Operation'] = [self.dpmb_location]
        results['Program'] = [self.dpmb_program]
        results['SSPEC'] = [self.dpmb_qdf]
        results['DevRevStep'] = [self.dpmb_step]
        results['TestName'] = [data['TestName'][0] if data['TestName'] else " "] # need to update with first FAIL
        results['TestValue'] = [data['TestValue'][0] if data['TestValue'] else " "] # Need to update with first FAIL
        results['DB'] = [debuglog[dpmb_sequence][0] if len(debuglog) > 0 else  " "]  
        results['BinDesc'] = [debuglog[dpmb_sequence][1] if len(debuglog) > 0 else " "]

        # Fill Final Bin Dictionary missing keys
        final_bin['VisualId'] = dpmb_vid

        self.files[f'{dpmb_sequence}_{zip_path}'] = pd.DataFrame(data)
        self.binfiles[f'{dpmb_sequence}_{zip_path}'] = pd.DataFrame(final_bin)
        self.resultsfiles[f'{dpmb_sequence}_{zip_path}'] = pd.DataFrame(results)

        #self.ppv_Cols = ['VisualId','DpmBucket','DecimaSite','DecimaWW','DecimaBucket','DpmBucketAccuracy','ProductConfigurationName']

        ## Increase seq key on each folder checked
        self.UnitTestingSeqKey += 1

        return dpmb_data 
                    #dpmb_data += [zip_path.rstrip('.zip')] + [folder] + parse_line(line)
                    #dpmb_data = [zip_path.rstrip('.zip')] + [folder] + parse_line(line) for line in lines if search_string in line and parse_line(line) is not None]
        
        
        #return [[zip_path.rstrip('.zip')] + [folder] + parse_line(line) for line in lines if search_string in line and parse_line(line) is not None]

    def search_in_debug_file(self, file_path, search_string, zip_path):
        folder = os.path.dirname(file_path).split('\\')[-1]
        env = ['Location Code:', 'SSPEC:','Lot Name:']
        data = {'VisualId':[],'DpmBucket':[],'DecimaSite':[],'DecimaWW':[],'DecimaBucket':[],'DpmBucketAccuracy':[],'ProductConfigurationName':[],'BinDesc':[]}
        BinDesc = []
        
        with open(file_path, 'r', encoding= 'utf-8') as file:
            content = file.read()

            parts = content.split(self.unitstart)
            #lines = file                      

            for part in parts:
                lines = part.split('\n')
                
                for line in lines:
                
                    if search_string in line:
                        bindesc = line.split(search_string)[-1].split(" ")
                        binnum = bindesc[0].strip()
                        binname = bindesc[-1].strip("(").strip(")")
                        BinDesc.append([binnum, binname])


        #data['BinDesc'] += [BinDesc]
        #self.ppvfiles[f'{zip_path}'] = data

        return BinDesc 
                    #dpmb_data += [zip_path.rstrip('.zip')] + [folder] + parse_line(line)
                    #dpmb_data = [zip_path.rstrip('.zip')] + [folder] + parse_line(line) for line in lines if search_string in line and parse_line(line) is not None]
        
        
        #return [[zip_path.rstrip('.zip')] + [folder] + parse_line(line) for line in lines if search_string in line and parse_line(line) is not None]

    def search_in_directory(self, directory_path, search_string, zip_path=None):
        data = []
        ## This is mainly to change how data is used when using zipfile option
        usebasefolder = False
        if zip_path == None:
            usebasefolder = True    
        
        for root, dirs, files in os.walk(directory_path):

            for ddfile in files:
                if ddfile == 'DebugLog.txt':
                    dfile_path = os.path.join(root, ddfile)
                    if usebasefolder: zip_path = root.split("\\")[-1]
                    print(f'MSG-- DebugLog file found at location: {dfile_path}. Looking for bin descriptions...')
                    pdata = self.search_in_debug_file(file_path=dfile_path, search_string=self.bin_string, zip_path=zip_path)

            for dir in dirs:
                
                # Flag to check if we are inside the same Folder in case of multiple loops
                self.infolder = False                   
                if dir == 'UnitLogs':
                    # Start counting for all the files found
                    seq = 0
                    self.infolder = True
                    for droot, ddirs, dfiles in os.walk(root):
                        for file in dfiles:
                            if file == 'PythonLog.txt':
                                
                                if usebasefolder: zip_path = root.split("\\")[-1]
                                file_path = os.path.join(droot, file)
                                print(f'MSG-- Python Log file found at location: {file_path}. Looking for unit sequence data...')
                                #print(f'MSG-- PPV Logs file found in folder {file_path}-- Searching for data...')
                                data = self.search_in_file(file_path, search_string, zip_path, pdata, seq)
                                # Increment the sequence for each file found
                                seq += 1
                    # Incresease LotsSeq for each UnitLogs Folder Found
                    self.LotsSeqKey += 1   

        return data

    def search_in_zip(self, zip_path, temp_path, search_string):
        #temp_dir = os.path.dirname(os.path.realpath(__file__))
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_path)
        return self.search_in_directory(temp_path, search_string, os.path.basename(zip_path))

    def search_in_folder(self, folder_path, search_string):
        data = []
        
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
                     
            if zipfile.is_zipfile(item_path) and '.zip' in item:
                temp_name = os.path.basename(item).replace('.zip', '')
                temp_path = os.path.join(folder_path, temp_name)
                print(f'MSG-- Working on file {item_path}, saving temp data in {temp_path}')
                data = self.search_in_zip(item_path, temp_path, search_string)
                if not data:
                    print(f'No data found for file {item_path}')
                print(f'MSG-- Removing temporal folder for file {item_path}, --> {temp_path}')
                shutil.rmtree(temp_path)    
        #return data


if __name__ == "__main__":
    args = argparser(debug)
    folder_path = args.folder #r'Q:\jfnavarr\GNR\IDI_PTC_LOGS\Bump100mV_CFC_IA'
    output_file = args.output #r'C:\ParsingFiles\PPV_Loops_Parser\Bump100mV_CFC_IA_Loops.xlsx'
    SeqKey = args.key
    bucket = args.bucket #'UNCORE.CHA.TORTO'
    WW = args.WW #'202440'
    zipf = args.zfile #False

    ptclog = LogsPTC(StartWW = WW, bucket = bucket, LotsSeqKey = SeqKey, folder_path=folder_path, output_file=output_file, zipfile=zipf)
    ptclog.run()

