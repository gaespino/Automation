
from __future__ import annotations
from abc import ABC, abstractmethod

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
	def __init__(self,Framework,Experiment:dict,outputNodeMap:dict[int,FlowInstance]):

		#Fixed Init Attributes
		self.outputPort:int=0
		self.runStatusHistory=[]

		#Entry Attributes
		self.Experiment=Experiment
		self.Framework=Framework
		self.outputNodeMap=outputNodeMap
		self.S2T_CONFIG = Framework.system_2_tester_default() if Framework != None else S2T_CONFIGURATION
		

	def runExperiment(self):
		self.runStatusHistory=self.Framework.RecipeExecutor(self.Experiment, S2T_BOOT_CONFIG = self.S2T_CONFIG, summary=True, cancel_flag = None)
		self.setOutputPort() # Determine instance output port
		self.jumpNextNode()# Run the next test in flow
	
	@abstractmethod
	def setOutputPort(self):
		pass

	def jumpNextNode(self):

		if(self.outputNodeMap): ##If there is no following nodes, it means its an endnode 
			return
		try:
			nextNode = self.outputNodeMap[self.outputPort]
			nextNode.runExperiment()
		except(IndexError):
			self.Framework.FrameworkPrint(f">>> Output Port Error: No handler found for port {self.outputPort}")

class singleFailFlowInstance(FlowInstance):
	def setOutputPort(self):
		return 0 if 'FAIL' in self.runStatusHistory else 1
	

class allFailFlowInstance(FlowInstance):
	def setOutputPort(self):
		return 0 if'FAIL' in self.runStatusHistory and len(set(self.runStatusHistory)) <=1 else 1
	
class mayorityFailFlowInstance(FlowInstance):
	def setOutputPort(self):
		return 0 if self.runStatusHistory.count('FAIL') >= len(self.runStatusHistory)/2 else 1

	
