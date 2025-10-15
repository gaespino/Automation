import os
import sys
import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod

# Setup paths for current and parent directories, and add parent directory to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

# Test Variables
def test_runStatusHistory(ID):
    
    if '1' in ID:
        FAIL = True
    if '2' in ID:
        FAIL = False    
    if '3' in ID:
        FAIL = True
    else:
        FAIL = False    
    return ['FAIL' if FAIL else 'PASS']

# Import FileHandler module for loading JSON files
import FileHandler as fh  # Assuming FileHandler contains functions for loading JSON

# Default configuration for System-to-Tester communication
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
    """
    Base class representing a flow instance. It is an abstract class that requires subclasses to implement specific behavior.

    Parameters:
    - ID: Unique identifier for the flow instance.
    - Name: Name of the flow instance.
    - Framework: Framework object to execute recipes.
    - Experiment: Contains experiment details/configuration.
    - outputNodeMap: Dict mapping output ports to corresponding nodes.
    - logger: Function or callable object used for logging (default: print).
    """

    def __init__(self, ID, Name, Framework, Experiment, outputNodeMap, logger=None):
        self.ID = ID
        self.Name = Name
        self.Framework = Framework
        self.Experiment = Experiment
        self.outputNodeMap = outputNodeMap
        self.outputPort = 0  # Default output port
        self.runStatusHistory = []  # History of run statuses
       
        if not logger: 
            logger = print
        self.logger = logger

        # Initialize system-to-tester configuration
        self.S2T_CONFIG = Framework.system_2_tester_default() if Framework else S2T_CONFIGURATION

    def run_experiment(self):
        """
        Executes the experiment associated with this flow instance using the Framework's RecipeExecutor.
        Logs the experiment execution start message, updates the runStatusHistory, and sets the output port.
        """
        self.logger(f"Running Experiment: {self.Name}")
        if self.Framework != None:
            self.runStatusHistory = self.Framework.RecipeExecutor(
            self.Experiment, S2T_BOOT_CONFIG=self.S2T_CONFIG, summary=True, cancel_flag=None)
        else:
            
            self.runStatusHistory = test_runStatusHistory(self.ID)
            
            print(self.runStatusHistory, self.ID)
        self.set_output_port()

    @abstractmethod
    def set_output_port(self):
        """
        Abstract method for setting the output port based on the run status.
        Subclasses must implement this method to determine specific output behavior.
        """
        pass

    def get_next_node(self):
        """
        Returns the next node to execute based on the output port determined in `set_output_port`.
        Logs an error if no handler is found for the current output port.
        """
        if self.outputNodeMap: 
            try:
                nextNode = self.outputNodeMap[self.outputPort]
                return nextNode
            except KeyError as e:
                self.logger(f"Output Port Error: No handler found for port {self.outputPort}. Exception: {e}")

class SingleFailFlowInstance(FlowInstance):
    def set_output_port(self):
        """
        Sets the output port based on the run status history.
        Returns 0 if 'FAIL' is found in the run status history, otherwise returns 1.
        """
        return 0 if 'FAIL' in self.runStatusHistory else 1

class AllFailFlowInstance(FlowInstance):
    def set_output_port(self):
        """
        Sets the output port based on the run status history.
        Returns 0 if all statuses are 'FAIL' or there is only one unique 'FAIL', otherwise returns 1.
        """
        return 0 if 'FAIL' in self.runStatusHistory and len(set(self.runStatusHistory)) <= 1 else 1

class MajorityFailFlowInstance(FlowInstance):
    def set_output_port(self):
        """
        Sets the output port based on the run status history.
        Returns 0 if the count of 'FAIL' is at least half or more of the total run status history, 
        else returns 1.
        """
        return 0 if self.runStatusHistory.count('FAIL') >= len(self.runStatusHistory) / 2 else 1

class FlowTestExecutor:
    """
    Executes a series of flow test instances starting from the root node.

    Parameters:
    - root: The root node from which to start the execution.
    """

    def __init__(self, root):
        self.root = root

    def execute(self):
        """
        Iteratively runs experiments for nodes starting from the root,
        and moves to the next node using `get_next_node` until no further nodes exist.
        """
        current_node = self.root
        while current_node is not None:
            current_node.run_experiment()
            current_node = current_node.get_next_node()

class FlowTestBuilder:
    """
    Builds flow tests by loading configuration files and constructing flow instances.

    Parameters:
    - structureFilePath: Path to the JSON file describing the flow structure.
    - flowsFilePath: Path to the JSON file describing the flow details/configuration.
    - iniFilePath: Path to the ini file describing additional configuration.
    - Framework: Optional framework instance for executing flow recipes.
    - logger: Optional logger (default: print).
    """

    def __init__(self, structureFilePath:str, flowsFilePath:str, iniFilePath:str, Framework=None, logger=None):
        if not logger: logger = print
        self.logger = logger

        self.structureFilePath = structureFilePath
        self.flowsFilePath = flowsFilePath
        self.iniFilePath=iniFilePath
        self.Framework = Framework

        # Load JSON and ini files to dictionaries
        self.structureFile = fh.load_json(structureFilePath)
        self.flowsFile = fh.load_json(flowsFilePath)
        self.initFile = fh.ini_to_dict_with_types(iniFilePath, convert_key_underscores=True)

        # Dictionary to store built nodes
        self.builtNodes = {}

        # Color constants for display
        self.status_colors = {'default': 'gray', 'running': 'blue', 'success': 'green', 'failed': 'red'}
        self.connection_colors = ['orange', 'purple', 'yellow', 'brown']
        self.node_width, self.node_height = 70, 120  # Node dimensions
        self.square_size = 15

    def build_flow(self, rootID):
        """
        Builds and returns an executor for the flow starting at rootID.

        Parameters:
        - rootID: The identifier for the root flow node to start building from.
        """
        root = self.__build_instance(rootID)
        return FlowTestExecutor(root=root)

    def __build_instance(self, flowKey):
        """
        Builds a flow instance node based on the provided flowKey,
        configuring it with the corresponding experiment info and output nodes.

        Parameters:
        - flowKey: Identifier for the flow node to build.
        """
        if flowKey in self.builtNodes.keys():
            node = self.builtNodes[flowKey]
        else:
            nodeConfig = self.structureFile[flowKey]
            ExperimentInfo = self.flowsFile[nodeConfig["flow"]]
            
            ExperimentIni = self.initFile[nodeConfig["flow"]]
            ExperimentInfo = {**ExperimentInfo , **ExperimentIni}

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
        """
        Recursively builds and returns mappings for the output nodes.

        Parameters:
        - nodeMap: Dictionary mapping output ports to subsequent node identifiers.
        """
        outputNodeMap = {}
        if nodeMap:
            for port, nodeKey in nodeMap.items():
                outputNodeMap[int(port)] = self.__build_instance(nodeKey)
        return outputNodeMap

    def create_interface(self, root_node):
        """
        Creates a graphical interface using Tkinter for visualizing flow progress, displaying nodes and connections.

        Parameters:
        - root_node: The root node from where the interface visualization begins.
        """
        root = tk.Tk()
        root.geometry("1400x1000")  # Larger window size for visualization
        root.title("Flow Progress Interface")
        container = ttk.Frame(root)
        container.pack(expand=True, fill='both')
        canvas = tk.Canvas(container, width=1400, height=1000)  # Large canvas
        canvas.pack(expand=True, fill='both')

        # Dict for storing node positions
        node_positions = {}
        spacing_x, spacing_y = 250, 200
        
        def draw_node(node, x, y):
            """
            Draws a node on the canvas at specified coordinates (x, y).
            Wraps the text within the node if necessary.

            Parameters:
            - node: The flow instance node to render.
            - x, y: The coordinates to position the node.
            """
            node_id = canvas.create_rectangle(x, y, x+self.node_width, y+self.node_height, fill=self.status_colors['default'], outline="black")
            small_square = canvas.create_rectangle(x+self.node_width-self.square_size, y, x+self.node_width, y+self.square_size, fill="white", outline="black")
            text_id = canvas.create_text(x+self.node_width/2, y+self.node_height/2, text=node.Name, fill="white", width=self.node_width-10)
            node_positions[node.ID] = {'position': (x, y), 'node_id': node_id, 'text_id': text_id, 'small_square': small_square}
            return node_id

        def draw_all_nodes():
            """
            Draws all flow nodes on the canvas, maintaining spacing to avoid overlap.
            """
            position_x, position_y = 50, 50
            for node in self.builtNodes.values():
                draw_node(node, position_x, position_y)
                position_x += spacing_x
                if position_x + self.node_width >= 1400:  # Edge boundary check
                    position_x = 50
                    position_y += spacing_y

        def draw_connections():
            """
            Draws connections between nodes using lines on the canvas.
            """
            for node in self.builtNodes.values():
                x, y = node_positions[node.ID]['position']
                for port, next_node in node.outputNodeMap.items():
                    next_x, next_y = node_positions[next_node.ID]['position']
                    connection_color = self.connection_colors[port % len(self.connection_colors)]
                    
                    # Draw connections with intermediary points to route around nodes
                    mid_x = (x + self.node_width + next_x) / 2
                    mid_y = y + spacing_y / 2
                    
                    canvas.create_line(x + self.node_width, y + self.square_size / 2, mid_x, y, fill=connection_color, width=2)
                    canvas.create_line(mid_x, y, mid_x, mid_y, fill=connection_color, width=2)
                    canvas.create_line(mid_x, mid_y, next_x, mid_y, fill=connection_color, width=2)
                    canvas.create_line(next_x, mid_y, next_x, next_y + self.square_size / 2, fill=connection_color, width=2)

        draw_all_nodes()
        draw_connections()
        root.mainloop()


def start_automation_flow(structure_path,flows_path,ini_file_path,framework):
    builder = FlowTestBuilder(structure_path, flows_path,ini_file_path, Framework=framework)
    executor = builder.build_flow(rootID='BASELINE')  # Ensure 'BASELINE' is a valid root node ID from your structure
    executor.execute()

# Instantiation and execution
if __name__ == '__main__':
    structure_path = r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\dummy_structure.json"
    flows_path = r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\Flows.json"
    iniFilePath = r"Q:\Gaespino\scripts\s2t\BASELINE\DebugFramework\Automation_Flow\example.ini"
    framework = None  # Assuming your framework instance

    builder = FlowTestBuilder(structure_path, flows_path,iniFilePath, Framework=framework)
    executor = builder.build_flow(rootID='BASELINE')  # Ensure 'BASELINE' is a valid root node ID from your structure
    executor.execute()