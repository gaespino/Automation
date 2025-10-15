import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time

#from users.gaespino.dev.DebugFramework.SerialConnection import teraterm
try:from users.gaespino.DebugFramework.FileHandler import printlog
except: 
    printlog = None
    print(' Logger not imported')
class TeratermTesterGUI:
    def __init__(self, root, data=None, teraterm=None):
        self.root = root
        self.root.title("Framework Serial Connnection Tests")
        self.Started = False
        self.BootStarted = False
        self.teraterm = teraterm
        # Initialize variables
        self.visual_var = tk.StringVar(value=data.get('Visual ID', '') if data!= None else data)
        self.bucket_var = tk.StringVar(value=data.get('Bucket', '') if data!= None else data)
        self.log_var = tk.StringVar(value=r'C:\Temp\capture.log')
        self.cmds_var = tk.StringVar(value=data.get('TTL Folder', '') if data!= None else data)
        self.test_var = tk.StringVar(value=data.get('Test Name', '') if data!= None else data)
        self.ttime_var = tk.IntVar(value=data.get('Test Time', 30) if data!= None else 30)
        self.tnum_var = tk.IntVar(value=data.get('Test Number', 1) if data!= None else 1)
        self.chkcore_var = tk.IntVar(value=data.get('Check Core', '') if data!= None else '')
        self.content_var = tk.StringVar(value=data.get('Content', '') if data!= None else 'Dragon')
        self.host_var = tk.StringVar(value=data.get('IP Address', '') if data!= None else '192.168.0.2')
        self.comport = tk.StringVar(value=data.get('COM Port', '') if data!= None else 8)
        self.qdf_var = tk.StringVar(value='NA')
        self.passtring = tk.StringVar(value=data.get('Pass String', 'Test Complete') if data!= None else 'Test Complete')
        self.failstring = tk.StringVar(value=data.get('Fail String', 'Test Failed') if data!= None else 'Test Failed')
        self.console_log_path = r'C:\Temp\TTL_Test.log'
        if printlog != None:
            self.logger = printlog(self.console_log_path)  #None  # Set to None for default print
            # Init Logger
            self.logger.initlog()
            self.debuglog_var = self.logger.Debuglog
        else:
            self.debuglog_var = None
        # Create input fields
        self.create_input_field("Visual", self.visual_var, 1, 0)
        self.create_input_field("Bucket", self.bucket_var, 1, 2)
        self.create_input_field("QDF:", self.qdf_var, 1, 4)

        self.create_input_field("CheckCore", self.chkcore_var, 2, 2)


        self.create_input_field("Test Time", self.ttime_var, 4, 2)
        self.create_input_field("Test Number", self.tnum_var, 4, 0)

        self.create_input_field("Pass String:", self.passtring, 5, 0)
        self.create_input_field("Fail String:", self.failstring, 5, 2)

        # Create test field with columnspan
        tk.Label(self.root, text="Test Name").grid(row=3, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.test_var).grid(row=3, column=1, columnspan=4, padx=5, pady=5, sticky="ew")
        
        # Create path selection
        self.path_button = tk.Button(root, text="TTL Macro Path", command=self.select_path)
        self.path_button.grid(row=6, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.cmds_var, state='readonly').grid(row=6, column=1, columnspan=4, padx=5, pady=5, sticky="ew")
        
        # Create content selection
        tk.Label(self.root, text="Content").grid(row=2, column=0, padx=5, pady=5)
        ttk.Combobox(self.root, textvariable=self.content_var, values=["Dragon", "Linux"]).grid(row=2, column=1, padx=5, pady=5)
        
        # Create host input
        self.create_input_field("Host", self.host_var, 0, 0)
        self.create_input_field("COM Port", self.comport, 0, 2)   

        # Create buttons
        self.start_button = tk.Button(root, text="CMDs Test", command=self.show_summary)
        self.start_button.grid(row=7, column=2, columnspan=1, padx=5, pady=5, sticky="ew")

        # Create buttons
        self.boot_button = tk.Button(root, text="Boot Log", command=self.boot_test)
        self.boot_button.grid(row=7, column=3, columnspan=1, padx=5, pady=5, sticky="ew")
                
        self.stop_button = tk.Button(root, state= "disabled", text="Stop Test", command=self.stop_test)
        self.stop_button.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        
        self.exit_button = tk.Button(root, text="Exit", command=self.exit_program)
        self.exit_button.grid(row=7, column=0, padx=5, pady=5, sticky="ew")
        
    def create_input_field(self, label, variable, row, column):
        tk.Label(self.root, text=label).grid(row=row, column=column, padx=5, pady=5)
        tk.Entry(self.root, textvariable=variable).grid(row=row, column=column+1, padx=5, pady=5)
        
    def select_path(self):
        # Open file dialog to select path
        path = filedialog.askdirectory()
        if path:
            self.cmds_var.set(path)
            self.fill_macro_files(path)
        
    def fill_macro_files(self, path):
        # Fill macro_files dictionary
        self.macro_files = {
            'Disconnect': rf'{path}\disconnect.ttl',
            'Connect': rf'{path}\connect.ttl',
            'StartCapture': rf'{path}\Boot.ttl',
            'StartTest': rf'{path}\Commands.ttl',
            'StopCapture': rf'{path}\stop_capture.ttl'
        }
        
    def show_summary(self):
        # Display summary of selected options
        summary = (
            f"Visual: {self.visual_var.get()}\n",
            f"QDF: {self.qdf_var.get()}\n",
            f"Bucket: {self.bucket_var.get()}\n",
            f"Log File: {self.log_var.get()}\n",
            f"Test: {self.test_var.get()}\n",
            f"Test Time: {self.ttime_var.get()}\n",
            f"Test Number: {self.tnum_var.get()}\n",
            f"CheckCore: {self.chkcore_var.get()}\n",
            f"Content: {self.content_var.get()}\n",
            f"Host: {self.host_var.get()}\n",
            f"Com Port: {self.comport.get()}\n",
            f"Macro Path: {self.cmds_var.get()}\n",
            f"Pass String: {self.passtring.get()}\n",
            f"Fail String: {self.failstring.get()}\n",
        )
        messagebox.showinfo("Summary", summary)
        
        # Ask for confirmation
        if messagebox.askokcancel("Confirmation", "Do you want to start the test?"):
            self.start_test()
        
    def start_test(self):
        # Initialize teraterm instance
        # (visual, qdf, bucket, log, macro_files, tfolder, test, ttime, tnum, DebugLog, chkcore=None, content=content, host = host, PassString = PassString, FailString = FailString)
        debug_log = self.debuglog_var if self.debuglog_var else print
        self.teraterm_instance = self.teraterm(
            visual=self.visual_var.get(),
            qdf=self.qdf_var.get(),
            bucket=self.bucket_var.get(),
            log=self.log_var.get(),
            cmds=self.macro_files,
            tfolder=r'C:\Temp',
            test=self.test_var.get(),
            ttime=self.ttime_var.get(),
            tnum=self.tnum_var.get(),
            DebugLog=debug_log,
            chkcore=self.chkcore_var.get(),
            content=self.content_var.get(),
            host=self.host_var.get(),
            PassString = self.passtring.get(),
            FailString =self.failstring.get()
        )
        # Run the test
        self.Started = True
        self.stop_button.config(state='active')
        self.boot_button.config(state=tk.DISABLED)
        self.teraterm_instance.run()

        
    def boot_test(self):
        # Initialize teraterm instance
        # (visual, qdf, bucket, log, macro_files, tfolder, test, ttime, tnum, DebugLog, chkcore=None, content=content, host = host, PassString = PassString, FailString = FailString)
        debug_log = self.debuglog_var if self.debuglog_var else print
        self.teraterm_instance = self.teraterm(
            visual=self.visual_var.get(),
            qdf=self.qdf_var.get(),
            bucket=self.bucket_var.get(),
            log=self.log_var.get(),
            cmds=self.macro_files,
            tfolder=r'C:\Temp',
            test=self.test_var.get(),
            ttime=self.ttime_var.get(),
            tnum=self.tnum_var.get(),
            DebugLog=debug_log,
            chkcore=self.chkcore_var.get(),
            content=self.content_var.get(),
            host=self.host_var.get(),
            PassString = self.passtring.get(),
            FailString =self.failstring.get()
        )
        # Run the test
        self.BootStarted = True
        self.stop_button.config(state='active')
        self.start_button.config(state=tk.DISABLED)
        self.teraterm_instance.boot_start()
        
        for i in range(30):
            print(f'Testing Connectio to Teraterm: Closing in: {30-i}')
            time.sleep(1)
            
        self.teraterm_instance.boot_end()
        #pass
    def stop_test(self):
        # Stop the test
        if self.BootStarted:
            self.teraterm_instance.terminate.set()  
            self.start_button.config(state=tk.ACTIVE)
            self.BootStarted =False  
        else: 
            self.teraterm_instance.boot_end()    
            self.boot_button.config(state=tk.ACTIVE)
            self.Started = False    
        self.stop_button.config(state='disabled')
        #pass
        
    def exit_program(self):
        # Exit the program
        if self.Started: self.stop_test()
        self.root.destroy()

def call(root=None, data=None, teraterm=None):
    # Create main window
    if root == None: root = tk.Tk()
    app = TeratermTesterGUI(root, data, teraterm)
    root.mainloop()

if __name__ == "__main__":
    call()
