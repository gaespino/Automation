
from __future__ import annotations
from abc import ABC, abstractmethod
import os
import sys

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

import FileHandler as fh

##Default Init
S2T_CONFIGURATION = {
	'AFTER_MRC_POST': 0xbf000000,
	'EFI_POST': 0xef0000ff,
	'LINUX_POST': 0x58000000,
	'BOOTSCRIPT_RETRY_TIMES': 3,
	'BOOTSCRIPT_RETRY_DELAY': 60,
	'MRC_POSTCODE_WT': 30,
	'EFI_POSTCODE_WT': 60,
	'MRC_POSTCODE_CHECK_COUNT': 5,
	'EFI_POSTCODE_CHECK_COUNT': 10,
	'BOOT_STOP_POSTCODE' : 0x0,
	'BOOT_POSTCODE_WT' : 30,
	'BOOT_POSTCODE_CHECK_COUNT' : 1
}


##SmartFlow Objects
class FlowInstance(ABC):
	def __init__(self,ID,Name:str,Framework,Experiment:dict,outputNodeMap:dict[int,FlowInstance],logger=None):

		#Setting Logger
		if not logger:logger=print
		self.logger=logger

		#Fixed Init Attributes
		self.outputPort:int=0
		self.runStatusHistory=[]

		#Entry Attributes
		self.Experiment=Experiment
		self.Framework=Framework
		self.outputNodeMap=outputNodeMap
		self.Name=Name
		self.ID=ID
		self.S2T_CONFIG = Framework.system_2_tester_default() if Framework != None else S2T_CONFIGURATION
		

	def run_experiment(self):
		self.logger(f"Running Experiment: {self.Name}")
		self.runStatusHistory=self.Framework.RecipeExecutor(self.Experiment, S2T_BOOT_CONFIG = self.S2T_CONFIG, summary=True, cancel_flag = None)
		#self.runStatusHistory=['FAIL']
		self.set_output_port() # Determine instance output port
	
	@abstractmethod
	def set_output_port(self):
		pass

	def get_next_node(self):

		if(self.outputNodeMap): ##Follow only if its not falsy value. Will stop with none of empty dict 
			try:
				nextNode = self.outputNodeMap[self.outputPort]
				return nextNode
			except(IndexError):
				self.Framework.FrameworkPrint(f">>> Output Port Error: No handler found for port {self.outputPort}")

class singleFailFlowInstance(FlowInstance):
	def set_output_port(self):
		return 0 if 'FAIL' in self.runStatusHistory else 1

class allFailFlowInstance(FlowInstance):
	def set_output_port(self):
		return 0 if'FAIL' in self.runStatusHistory and len(set(self.runStatusHistory)) <=1 else 1
	
class mayorityFailFlowInstance(FlowInstance):
	def set_output_port(self):
		return 0 if self.runStatusHistory.count('FAIL') >= len(self.runStatusHistory)/2 else 1
	



class FlowTestExecutor:

	def __init__(self,root:FlowInstance):
		self.root=root
		self.currentNode=root
	
	def step(self):
		self.currentNode.run_experiment()

		#ADD A CALLBACK FOR ANY DEBUG MESSAGES
		self.currentNode=self.currentNode.get_next_node()
	
	def restart_flow(self):
		self.currentNode=self.root
	
	def run_flow(self):
		while(self.currentNode):
			self.step()
	

class FlowTestBuilder:

	def __init__(self,structureFilePath:str,flowsFilePath,Framework=None,logger=None):

		#Setting Logger
		if not logger:logger=print
		self.logger=logger

		self.structureFilePath=structureFilePath
		self.flowsFilePath=flowsFilePath
		self.Framework=Framework


		#Loading Dicts
		self.structureFile=fh.load_json(structureFilePath)
		self.flowsFile=fh.load_json(flowsFilePath)

		#built nodes
		self.builtNodes={}
	
	def build_flow(self,rootID):
		root=self.__build_instance(rootID)
		return FlowTestExecutor(root=root)

	def __build_instance(self,flowKey):
		if(flowKey in self.builtNodes.keys()):
			node=self.builtNodes[flowKey]
		else:
			print(f"Building Flow {flowKey}")
			nodeConfig=self.structureFile[flowKey] #Loading Node Structure
			ExperimentInfo=self.flowsFile[nodeConfig["flow"]] # Loading Experiment dict
			flowClass=globals()[nodeConfig["instanceType"]] # Setting the flow class which will be used
			outputNodeMap=self.__build_following_nodes(nodeConfig["outputNodeMap"]) # setting node's output map
			node=flowClass(										 #Creating FlowInstance
				ID=flowKey,
				Name=nodeConfig["name"],
				Framework=self.Framework,
				Experiment=ExperimentInfo,
				outputNodeMap=outputNodeMap,
				logger=self.logger
			)
			self.builtNodes[flowKey]=node #Saving node in the already built dict
		return node

	def __build_following_nodes(self,nodeMap:dict):
		outputNodeMap={}
		if(nodeMap):
			for port,nodeKey in nodeMap.items():
				outputNodeMap[int(port)]=self.__build_instance(nodeKey)
		return outputNodeMap
	

if __name__ == "__main__":
	structure_path=r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\dummy_structure.json"
	flows_path=r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\Flows.json"
	builder=FlowTestBuilder(structureFilePath=structure_path,flowsFilePath=flows_path)
	builder.build_flow("BASELINE").run_flow()
				





		





	
