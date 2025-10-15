import os
import sys
import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod

# Setup for current and parent directory paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

import FileHandler as fh  # Assuming FileHandler contains functions for loading JSON
#from .. import FileHandler as fh

# Default System-to-Tester Configuration
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
    'BOOT_STOP_POSTCODE': 0x0,
    'BOOT_POSTCODE_WT': 30,
    'BOOT_POSTCODE_CHECK_COUNT': 1
}

class FlowInstance(ABC):
    def __init__(self, ID, Name, Framework, Experiment, outputNodeMap, logger=None):
        self.ID = ID
        self.Name = Name
        self.Framework = Framework
        self.Experiment = Experiment
        self.outputNodeMap = outputNodeMap
        self.outputPort = 0
        self.runStatusHistory = []
        
        if not logger: 
            logger = print
        self.logger = logger

        self.S2T_CONFIG = Framework.system_2_tester_default() if Framework else S2T_CONFIGURATION

    def run_experiment(self):
        self.logger(f"Running Experiment: {self.Name}")
        #self.runStatusHistory=["FAIL"]
        self.runStatusHistory = self.Framework.RecipeExecutor(
            self.Experiment, S2T_BOOT_CONFIG=self.S2T_CONFIG, summary=True, cancel_flag=None)
        self.set_output_port()

    @abstractmethod
    def set_output_port(self):
        pass

    def get_next_node(self):
        if self.outputNodeMap: 
            try:
                nextNode = self.outputNodeMap[self.outputPort]
                return nextNode
            except KeyError as e:
                self.logger(f"Output Port Error: No handler found for port {self.outputPort}. Exception: {e}")

class SingleFailFlowInstance(FlowInstance):
    def set_output_port(self):
        return 0 if 'FAIL' in self.runStatusHistory else 1

class AllFailFlowInstance(FlowInstance):
    def set_output_port(self):
        return 0 if 'FAIL' in self.runStatusHistory and len(set(self.runStatusHistory)) <= 1 else 1

class MajorityFailFlowInstance(FlowInstance):
    def set_output_port(self):
        return 0 if self.runStatusHistory.count('FAIL') >= len(self.runStatusHistory) / 2 else 1

class FlowTestExecutor:
    def __init__(self, root):
        self.root = root

    def execute(self):
        current_node = self.root
        while current_node is not None:
            current_node.run_experiment()
            current_node = current_node.get_next_node()

class FlowTestBuilder:
    def __init__(self, structureFilePath:str, flowsFilePath:str,iniFilePath:str, Framework=None, logger=None):
        if not logger: logger = print
        self.logger = logger

        self.structureFilePath = structureFilePath
        self.flowsFilePath = flowsFilePath
        self.iniFilePath=iniFilePath
        self.Framework = Framework

        # Loading Dicts
        self.structureFile = fh.load_json(structureFilePath)
        self.flowsFile = fh.load_json(flowsFilePath)
        self.initFile=fh.ini_to_dict_with_types(iniFilePath,convert_key_underscores=True)

        # Built nodes
        self.builtNodes = {}

        # Constants for colors
        self.status_colors = {'default': 'gray', 'running': 'blue', 'success': 'green', 'failed': 'red'}
        self.connection_colors = ['orange', 'purple', 'yellow', 'brown']
        self.node_width, self.node_height = 70, 120  # Increased dimensions
        self.square_size = 15

    def build_flow(self, rootID):
        root = self.__build_instance(rootID)
        #self.create_interface(root)
        return FlowTestExecutor(root=root)

    def __build_instance(self, flowKey):
        if flowKey in self.builtNodes.keys():
            node = self.builtNodes[flowKey]
        else:
            nodeConfig = self.structureFile[flowKey]
            ExperimentInfo = self.flowsFile[nodeConfig["flow"]]
            
            ExperimentIni  = self.initFile[nodeConfig["flow"]]
            ExperimentInfo = {**ExperimentInfo , **ExperimentIni}
            #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            #print(ExperimentInfo)
            #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            flowClass = globals()[nodeConfig["instanceType"]]
            outputNodeMap = self.__build_following_nodes(nodeConfig["outputNodeMap"])
            node = flowClass(
                ID=flowKey,
                Name=nodeConfig["name"],
                Framework=self.Framework,
                Experiment=ExperimentInfo,
                outputNodeMap=outputNodeMap,
                logger=self.logger
            )
            self.builtNodes[flowKey] = node
        return node

    def __build_following_nodes(self, nodeMap:dict):
        outputNodeMap = {}
        if nodeMap:
            for port, nodeKey in nodeMap.items():
                outputNodeMap[int(port)] = self.__build_instance(nodeKey)
        return outputNodeMap

    def create_interface(self, root_node):
        root = tk.Tk()
        root.geometry("1400x1000")  # Set a larger window size
        root.title("Flow Progress Interface")
        container = ttk.Frame(root)
        container.pack(expand=True, fill='both')
        canvas = tk.Canvas(container, width=1400, height=1000)  # Adjust canvas size
        canvas.pack(expand=True, fill='both')

        # Positioning helpers
        node_positions = {}
        spacing_x, spacing_y = 250, 200
        
        def draw_node(node, x, y):
            # Create a rectangle and a small square for connections
            node_id = canvas.create_rectangle(x, y, x+self.node_width, y+self.node_height, fill=self.status_colors['default'], outline="black")
            small_square = canvas.create_rectangle(x+self.node_width-self.square_size, y, x+self.node_width, y+self.square_size, fill="white", outline="black")
            
            # Wrap text if longer
            text_id = canvas.create_text(x+self.node_width/2, y+self.node_height/2, text=node.Name, fill="white", width=self.node_width-10)
            
            node_positions[node.ID] = {'position': (x, y), 'node_id': node_id, 'text_id': text_id, 'small_square': small_square}
            return node_id

        def draw_all_nodes():
            # Initial Position
            position_x, position_y = 50, 50
            
            # Draw nodes in rows, ensuring spacing to avoid overlap
            for node in self.builtNodes.values():
                draw_node(node, position_x, position_y)
                position_x += spacing_x
                if position_x + self.node_width >= 1400:  # Edge check
                    position_x = 50
                    position_y += spacing_y

        def draw_connections():
            for node in self.builtNodes.values():
                x, y = node_positions[node.ID]['position']
                for port, next_node in node.outputNodeMap.items():
                    next_x, next_y = node_positions[next_node.ID]['position']
                    connection_color = self.connection_colors[port % len(self.connection_colors)]
                    
                    # Path around boxes using intermediary points
                    mid_x = (x + self.node_width + next_x) / 2
                    mid_y = y + spacing_y / 2
                    
                    canvas.create_line(x + self.node_width, y + self.square_size / 2, mid_x, y, fill=connection_color, width=2)
                    canvas.create_line(mid_x, y, mid_x, mid_y, fill=connection_color, width=2)
                    canvas.create_line(mid_x, mid_y, next_x, mid_y, fill=connection_color, width=2)
                    canvas.create_line(next_x, mid_y, next_x, next_y + self.square_size / 2, fill=connection_color, width=2)

        draw_all_nodes()
        draw_connections()
        root.mainloop()

# Instantiation and execution
if __name__ == '__main__':
    structure_path = r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\dummy_structure.json"
    flows_path = r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\Flows.json"
    iniFilePath = r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\example.ini"
    framework = None  # Assuming your framework instance

    builder = FlowTestBuilder(structure_path, flows_path,iniFilePath, Framework=framework)
    executor = builder.build_flow(rootID='BASELINE')  # Ensure 'BASELINE' is a valid root node ID from your structure
    executor.execute()