import evg
import json

def DPMInstanceEdit():
    #namePath = 'Uncore'
    namePath = evg.GetFile("./Shared/Common/TPLOAD/DPMTPConfiguration.json")
    with open(namePath, 'r') as file: instances = json.load(file)
    #instances = {}

    for key in instances.keys():
        if instances[key]:
            evg.PrintToConsole("Setting Instances with DPM Configuration: '%s'\n" %key)
            dpmList = instances[key]['instance']
            dpmfctrack = instances[key]['masking']
            dpmPlist = instances[key]['plist']
            shmoo = instances[key]['shmoo']

            if dpmList:
                for ls in dpmList:
                    if dpmPlist: 
                        evg.PrintToConsole("DPM -- Modifying instance: %s ---> Patlist: %s\n" %(ls, dpmPlist))
                        evg.SetTestParamStr(ls,'Patlist', dpmList)
                    if shmoo:
                        evg.PrintToConsole("DPM -- Modifying instance: %s ---> LogLevel: %s\n" %(ls, "Enabled"))
                        evg.PrintToConsole("DPM -- Modifying instance: %s ---> ShmooEnable: %s\n" %(ls, "ENABLED_ALWAYS"))
                        evg.PrintToConsole("DPM -- Modifying instance: %s ---> ShmooConfigurationFile: %s\n" %(ls, shmoo))
                        evg.SetTestParamStr(ls,'LogLevel', "Enabled")
                        evg.SetTestParamStr(ls,'ShmooEnable', "ENABLED_ALWAYS")
                        evg.SetTestParamStr(ls,'ShmooConfigurationFile', shmoo)
                    
                    evg.VerifyTest(ls)
        
            if dpmfctrack:    
                for fc in dpmfctrack.keys():
                    evg.PrintToConsole("DPM -- Modifying instance: %s ---> ConfigFile: %s\n" %(fc, dpmfctrack[fc]))
                    evg.SetTestParamStr(fc,'ConfigFile', dpmfctrack[fc])
                    evg.VerifyTest(ls)
            
            evg.PrintToConsole("Setting Instances with DPM Configuration: '%s' Succesfull!! \n" %key)
