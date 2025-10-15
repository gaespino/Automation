import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import threading
import time
import datetime

class DataUploadUI:
    def __init__(self, root, datahandler=None):
        self.root = root
        self.datahandler = datahandler
        self.root.title("Data Upload & Summary Generator")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # Variables
        self.tfolder_var = tk.StringVar()
        self.visual_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.bucket_var = tk.StringVar()
        self.ww_var = tk.StringVar()
        self.product_var = tk.StringVar(value="GNR")  # Default to GNR
        self.upload_to_disk_var = tk.BooleanVar(value=True)
        self.upload_data_var = tk.BooleanVar(value=True)
        
        self.setup_ui()
        self.update_ww()  # Initialize WW value
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Folder selection
        ttk.Label(main_frame, text="Target Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.tfolder_var, state='readonly')
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1)
        
        # Search button
        self.search_btn = ttk.Button(main_frame, text="Search for Visual & Name", 
                                   command=self.search_data, state='disabled')
        self.search_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, 
                                                          sticky=(tk.W, tk.E), pady=10)
        
        # Found data section
        ttk.Label(main_frame, text="Found Data:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Visual field
        ttk.Label(main_frame, text="Visual ID:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.visual_entry = ttk.Entry(main_frame, textvariable=self.visual_var, state='readonly')
        self.visual_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Name field
        ttk.Label(main_frame, text="Name:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, state='readonly')
        self.name_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Bucket field (editable)
        ttk.Label(main_frame, text="Bucket:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.bucket_entry = ttk.Entry(main_frame, textvariable=self.bucket_var)
        self.bucket_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # WW field (editable)
        ttk.Label(main_frame, text="Work Week (WW):").grid(row=7, column=0, sticky=tk.W, pady=2)
        # WW spinbox (0-52) - now editable
        self.ww_spinbox = ttk.Spinbox(main_frame, from_=0, to=52, textvariable=self.ww_var, 
                                     width=10)
        self.ww_spinbox.grid(row=7, column=1, sticky=tk.W, pady=2)
        
        # Product selection
        ttk.Label(main_frame, text="Product:").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.product_combo = ttk.Combobox(main_frame, textvariable=self.product_var, 
                                         values=["GNR", "CWF"], state='readonly', width=10)
        self.product_combo.grid(row=8, column=1, sticky=tk.W, pady=2)
        
        # Options section
        ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, columnspan=2, 
                                                          sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(main_frame, text="Upload Options:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=10, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Checkboxes
        ttk.Checkbutton(main_frame, text="Upload to Disk", 
                       variable=self.upload_to_disk_var).grid(row=11, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(main_frame, text="Upload Data", 
                       variable=self.upload_data_var).grid(row=11, column=1, sticky=tk.W, pady=2)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)
        
        self.generate_btn = ttk.Button(button_frame, text="Generate Summary", 
                                     command=self.generate_summary, state='disabled')
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.upload_btn = ttk.Button(button_frame, text="Manual Upload", 
                                   command=self.manual_upload, state='disabled')
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_all_btn = ttk.Button(button_frame, text="Process All", 
                                        command=self.process_all, state='disabled')
        self.process_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Log output
        ttk.Label(main_frame, text="Output Log:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=13, column=0, columnspan=2, sticky=tk.W, pady=(20, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=8, width=70)
        self.log_text.grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure row weight for log expansion
        main_frame.rowconfigure(14, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=15, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def update_ww(self):
        """Update WW field based on current date"""
        try:
            ww = self.get_current_ww()
            self.ww_var.set(str(ww))
            self.log_message(f"Initialized Work Week to: {ww}")
            
        except Exception as e:
            self.log_message(f"Error updating WW: {str(e)}")
            # Fallback to WW 1 if there's an error
            self.ww_var.set("1")
    
    def get_current_ww(self):
        """Get current work week using the same logic as datahandler"""
        currentdate = datetime.date.today()
        iso_calendar = currentdate.isocalendar()
        return iso_calendar[1]
        
    def browse_folder(self):
        """Browse for target folder"""
        folder = filedialog.askdirectory(title="Select Target Folder")
        if folder:
            self.tfolder_var.set(folder)
            self.search_btn.config(state='normal')
            self.log_message(f"Selected folder: {folder}")
            
    def search_data(self):
        """Search for visual and name in the log file"""
        tfolder = self.tfolder_var.get()
        if not tfolder:
            messagebox.showerror("Error", "Please select a target folder first")
            return
            
        self.status_var.set("Searching for data...")
        self.log_message("Searching for visual and name data...")
        
        try:
            if self.datahandler is not None:
                # Use real datahandler function
                name_result = self.datahandler.search_exp_name(tfolder)
            else:
                # Dummy implementation for testing
                name_result = self.dummy_search_exp_name(tfolder)
            
            # Search for visual using regex
            visual_result = self.search_visual_id(tfolder)
            
            if name_result and visual_result:
                self.name_var.set(name_result)
                self.visual_var.set(visual_result)
                
                # Enable buttons
                self.generate_btn.config(state='normal')
                self.upload_btn.config(state='normal')
                self.process_all_btn.config(state='normal')
                
                self.log_message(f"Found Name: {name_result}")
                self.log_message(f"Found Visual ID: {visual_result}")
                self.status_var.set("Data found successfully")
                
            else:
                error_msg = "Could not find required data in log file"
                if not name_result:
                    error_msg += "\n- Name not found (pattern: -- Debug Framework (\\w+) ---)"
                if not visual_result:
                    error_msg += "\n- Visual ID not found (pattern: VisualID: (\\w+))"
                    
                messagebox.showerror("Search Error", error_msg)
                self.status_var.set("Search failed")
                
        except Exception as e:
            error_msg = f"Error during search: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.log_message(f"ERROR: {error_msg}")
            self.status_var.set("Search error")
    
    def dummy_search_exp_name(self, tfolder, logname='DebugFrameworkLogger.log'):
        """Dummy implementation for testing when datahandler is None"""
        self.log_message("DUMMY MODE: Simulating search for experiment name...")
        time.sleep(1)  # Simulate processing time
        
        # Try to find real file first, if not create dummy data
        try:
            log_file = os.path.join(tfolder, logname)
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                pattern = r"-- Debug Framework (\w+) ---"
                match = re.search(pattern, content)
                
                if match:
                    return match.group(1)
            
            # If no real file or pattern found, return dummy data
            self.log_message("DUMMY MODE: No real log file found, using dummy name")
            return "TestExperiment123"
            
        except Exception as e:
            self.log_message(f"DUMMY MODE: Error reading file, using dummy name: {str(e)}")
            return "TestExperiment123"
    
    def search_visual_id(self, tfolder, logname='DebugFrameworkLogger.log'):
        """Search for visual ID using regex"""
        try:
            log_file = os.path.join(tfolder, logname)
            if not os.path.exists(log_file):
                if self.datahandler is None:
                    # Dummy mode
                    self.log_message("DUMMY MODE: No log file found, using dummy visual ID")
                    return "VIS456789"
                return None
                
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simplified pattern - just look for VisualID: followed by the ID
            pattern = r"VisualID: (\w+)"
            match = re.search(pattern, content)
            
            if match:
                return match.group(1)
            elif self.datahandler is None:
                # Dummy mode - return dummy visual ID if pattern not found
                self.log_message("DUMMY MODE: Pattern not found, using dummy visual ID")
                return "VIS456789"
            return None
            
        except Exception as e:
            self.log_message(f"Error searching for visual ID: {str(e)}")
            if self.datahandler is None:
                self.log_message("DUMMY MODE: Using dummy visual ID due to error")
                return "VIS456789"
            return None
    
    def generate_summary(self):
        """Generate summary using the provided function"""
        if not self.validate_data():
            return
            
        self.status_var.set("Generating summary...")
        self.log_message("Starting summary generation...")
        
        def run_summary():
            try:
                if self.datahandler is not None:
                    # Call real datahandler function with all required parameters
                    self.datahandler.generate_summary(
                        visual=self.visual_var.get(),
                        bucket=self.bucket_var.get(),
                        name=self.name_var.get(),
                        WW=self.ww_var.get(),
                        product=self.product_var.get(),
                        tfolder=self.tfolder_var.get(),
                        logger=self.log_message
                    )
                else:
                    # Dummy implementation for testing
                    self.dummy_generate_summary()
                
                self.log_message("Summary generation completed successfully")
                self.status_var.set("Summary generated")
                
            except Exception as e:
                error_msg = f"Error generating summary: {str(e)}"
                self.log_message(f"ERROR: {error_msg}")
                self.status_var.set("Summary generation failed")
                messagebox.showerror("Error", error_msg)
        
        # Run in separate thread to prevent UI freezing
        threading.Thread(target=run_summary, daemon=True).start()
    
    def dummy_generate_summary(self):
        """Dummy implementation for testing"""
        self.log_message("DUMMY MODE: Starting summary generation...")
        self.log_message(f"DUMMY MODE: Visual ID: {self.visual_var.get()}")
        self.log_message(f"DUMMY MODE: Bucket: {self.bucket_var.get()}")
        self.log_message(f"DUMMY MODE: Name: {self.name_var.get()}")
        self.log_message(f"DUMMY MODE: Target folder: {self.tfolder_var.get()}")
        self.log_message(f"DUMMY MODE: Work Week: {self.ww_var.get()}")
        self.log_message(f"DUMMY MODE: Product: {self.product_var.get()}")
        
        # Simulate processing time
        for i in range(3):
            time.sleep(1)
            self.log_message(f"DUMMY MODE: Processing step {i+1}/3...")
        
        self.log_message("DUMMY MODE: Summary generation completed")
    
    def manual_upload(self):
        """Perform manual upload using the provided function"""
        if not self.validate_data():
            return
            
        self.status_var.set("Uploading data...")
        self.log_message("Starting manual upload...")
        
        def run_upload():
            try:
                if self.datahandler is not None:
                    # Call real datahandler function with all required parameters
                    self.datahandler.manual_upload(
                        tfolder=self.tfolder_var.get(),
                        visual=self.visual_var.get(),
                        Product=self.product_var.get(),
                        UPLOAD_TO_DISK=self.upload_to_disk_var.get(),
                        UPLOAD_DATA=self.upload_data_var.get(),
                        logger=self.log_message
                    )
                else:
                    # Dummy implementation for testing
                    self.dummy_manual_upload()
                
                self.log_message("Manual upload completed successfully")
                self.status_var.set("Upload completed")
                
            except Exception as e:
                error_msg = f"Error during upload: {str(e)}"
                self.log_message(f"ERROR: {error_msg}")
                self.status_var.set("Upload failed")
                messagebox.showerror("Error", error_msg)
        
        # Run in separate thread to prevent UI freezing
        threading.Thread(target=run_upload, daemon=True).start()
    
    def dummy_manual_upload(self):
        """Dummy implementation for testing"""
        self.log_message("DUMMY MODE: Starting manual upload...")
        self.log_message(f"DUMMY MODE: Target folder: {self.tfolder_var.get()}")
        self.log_message(f"DUMMY MODE: Visual ID: {self.visual_var.get()}")
        self.log_message(f"DUMMY MODE: Upload to disk: {self.upload_to_disk_var.get()}")
        self.log_message(f"DUMMY MODE: Upload data: {self.upload_data_var.get()}")
        self.log_message(f"DUMMY MODE: Work Week: {self.ww_var.get()}")
        self.log_message(f"DUMMY MODE: Product: {self.product_var.get()}")
        
        # Simulate upload process
        steps = ["Preparing files", "Validating data", "Uploading to disk", "Uploading data", "Finalizing"]
        for i, step in enumerate(steps):
            if i == 2 and not self.upload_to_disk_var.get():
                self.log_message(f"DUMMY MODE: Skipping step: {step}")
                continue
            if i == 3 and not self.upload_data_var.get():
                self.log_message(f"DUMMY MODE: Skipping step: {step}")
                continue
                
            time.sleep(0.8)
            self.log_message(f"DUMMY MODE: {step}...")
        
        self.log_message("DUMMY MODE: Manual upload completed")
    
    def process_all(self):
        """Generate summary and then perform upload"""
        if not self.validate_data():
            return
            
        self.status_var.set("Processing all...")
        self.log_message("Starting complete process (summary + upload)...")
        
        def run_all():
            try:
                # First generate summary
                self.log_message("Step 1: Generating summary...")
                if self.datahandler is not None:
                    self.datahandler.generate_summary(
                        visual=self.visual_var.get(),
                        bucket=self.bucket_var.get(),
                        name=self.name_var.get(),
                        WW=self.ww_var.get(),
                        product=self.product_var.get(),
                        tfolder=self.tfolder_var.get(),
                        logger=self.log_message
                    )
                else:
                    self.dummy_generate_summary()
                
                self.log_message("Step 2: Performing upload...")
                if self.datahandler is not None:
                    self.datahandler.manual_upload(
                        tfolder=self.tfolder_var.get(),
                        visual=self.visual_var.get(),
                        Product=self.product_var.get(),
                        UPLOAD_TO_DISK=self.upload_to_disk_var.get(),
                        UPLOAD_DATA=self.upload_data_var.get(),
                        logger=self.log_message
                    )
                else:
                    self.dummy_manual_upload()
                
                self.log_message("All processes completed successfully")
                self.status_var.set("All processes completed")
                
            except Exception as e:
                error_msg = f"Error during processing: {str(e)}"
                self.log_message(f"ERROR: {error_msg}")
                self.status_var.set("Processing failed")
                messagebox.showerror("Error", error_msg)
        
        # Run in separate thread to prevent UI freezing
        threading.Thread(target=run_all, daemon=True).start()
    
    def validate_data(self):
        """Validate that required data is available"""
        if not self.visual_var.get() or not self.name_var.get():
            messagebox.showerror("Validation Error", 
                               "Visual ID and Name are required. Please search for data first.")
            return False
        
        # Validate WW is within range
        try:
            ww = int(self.ww_var.get())
            if ww < 0 or ww > 52:
                messagebox.showerror("Validation Error", 
                                   "Work Week must be between 0 and 52.")
                return False
        except ValueError:
            messagebox.showerror("Validation Error", 
                               "Work Week must be a valid number.")
            return False
        
        return True
    
    def log_message(self, message):
        """Add message to log output"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

def main(datahandler = None):
    """Main function to run the UI"""
    root = tk.Tk()
    
    # For testing without datahandler, pass None
    # For production, pass your datahandler instance
      # Replace with your datahandler instance
    
    app = DataUploadUI(root, datahandler)
    root.mainloop()

if __name__ == "__main__":
    main()