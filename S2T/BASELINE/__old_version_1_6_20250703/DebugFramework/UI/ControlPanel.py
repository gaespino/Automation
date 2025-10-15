import asyncio.events
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import os
import pandas as pd
import time
import threading
import queue
import multiprocessing
from contextlib import contextmanager

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

import FileHandler as fh

# Default configuration dictionary
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
# Mapping of labels to configuration keys
CONFIG_LABELS = {
	'Bootscript retries': 'BOOTSCRIPT_RETRY_TIMES',
	'Bootscript retry PC delay': 'BOOTSCRIPT_RETRY_DELAY',
	'EFI Postcode': 'EFI_POST',
	'EFI Postcode Waittime': 'EFI_POSTCODE_WT',
	'EFI Postcode checks count': 'EFI_POSTCODE_CHECK_COUNT',
	'OTHER Postcode': 'LINUX_POST',
	'MRC Postcode': 'AFTER_MRC_POST',
	'MRC Postcode Waittime': 'MRC_POSTCODE_WT',
	'MRC Postcode checks count': 'MRC_POSTCODE_CHECK_COUNT',
	'Boot Break Postcode': 'BOOT_STOP_POSTCODE',
	'Boot Break Waittimet': 'BOOT_POSTCODE_WT',
	'Boot Break checks count': 'BOOT_POSTCODE_CHECK_COUNT'
}

# Select Execution Type Process or Threads ---
use_process = False

class TaskCancelledException(Exception):
	"""Execution Cancelled by User"""
	pass

class ThreadHandler(threading.Thread):
	def __init__(self, group = None, target = None, name = None, args = ..., kwargs = None, *, daemon = None,):# exception_queue = None):
		super().__init__(group, target, name, args, kwargs, daemon=daemon)
		self._stop_event = threading.Event()
		self.exception_queue = queue.Queue()# exception_queue if exception_queue != None else queue.Queue()
		#self._target = target
		#self._args = args
		#self._kwargs = kwargs
	
	def run(self):
		try:
			print(f"({self.name}) --> Started\n")
			#while not self._stop_event.is_set():
			if self._target:
				self._target(*self._args, **self._kwargs)
				print(f"({self.name}) --> Ended")
				
			#	time.sleep(1)
			
		except Exception as e:
			print(f'({self.name}) --> Exception:', e)
			self.exception_queue.put(e)
	
	def stop(self):
		print(f"\n({self.name}) --> Stop order received")
		self._stop_event.set()

	def forceStop(self):
		print(f"\n({self.name}) --> Force Stop order received")
		self._stop_event.set()
		self.exception_queue.put(TaskCancelledException(f"{self.name} Task Force Stop"))
		raise TaskCancelledException(f"{self.name} Task Force Stop")
		#self.exception_queue.put(e)

	def clear(self):
		self._stop_event.clear()

	def get_exception(self):
		"""Retrieve any exception raised during thread execution."""
		if not self.exception_queue.empty():
			return self.exception_queue.get()
		return None

class DebugFrameworkControlPanel:
	def __init__(self, root, Framework):
		self.root = root
		self.root.title("Debug Framework Control Panel")
		self.Framework = Framework() if Framework != None else None
		self.experiments = {}
		self.experiment_frames = []
		self.hold_active = False
		self.cancel_requested = threading.Event()
		self.exception_queue = queue.Queue()
		self.current_experiment_index = 0
		self.S2T_CONFIG = Framework.system_2_tester_default() if Framework != None else S2T_CONFIGURATION 			
		self.create_widgets()
	
	def create_widgets(self):
		# Main Title
		title_frame = tk.Frame(self.root)
		title_frame.pack(fill=tk.X, padx=10, pady=5)
		tk.Label(title_frame, text="Debug Framework Control Panel", font=("Arial", 16)).pack(side=tk.LEFT)

		# Status Label
		self.status_label = tk.Label(title_frame, padx=5, width=15,  text=" Ready ", bg="white", fg="black", font=("Arial", 12), relief=tk.GROOVE, borderwidth=2)
		self.status_label.pack(side=tk.RIGHT)

		# Settings Button
		settings_icon = tk.PhotoImage(file=os.path.join(parent_dir,'UI', "settings_icon.png"))  # Ensure you have an icon file
		settings_icon = settings_icon.subsample(3, 3)
		self.settings_button = tk.Button(title_frame, image=settings_icon, command=self.open_settings_window)
		self.settings_button.image = settings_icon  # Keep a reference to avoid garbage collection
		self.settings_button.pack(side=tk.RIGHT, padx=5)

		# Row 1: Entry to load the Experiments File
		self.file_frame = tk.Frame(self.root)
		self.file_frame.pack(fill=tk.X, padx=10, pady=5)

		tk.Label(self.file_frame, text="Experiments", width=15).pack(side=tk.LEFT)
		self.file_entry = tk.Entry(self.file_frame)
		self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
		tk.Button(self.file_frame, text="Browse", command=self.load_experiments_file).pack(side=tk.LEFT)
		
		# Row 2: Separator line
		tk.Frame(self.root, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=10, pady=5)
		
		# Experiment Rows (will be dynamically created)
		self.experiment_container = tk.Frame(self.root)
		self.experiment_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

		# Second to Last Row: Control Buttons
		self.misc_frame = tk.Frame(self.root)
		self.misc_frame.pack(fill=tk.X, padx=10, pady=5)

		tk.Button(self.misc_frame, text=" Test TTL ", width=30, command=self.test_ttl).pack(side=tk.RIGHT, padx=10)

		self.stop_on_fail_var = tk.BooleanVar(value=False)
		tk.Checkbutton(self.misc_frame, text="Stop on Fail", variable=self.stop_on_fail_var).pack(side=tk.RIGHT)

		# Last Row: Control Buttons
		self.control_frame = tk.Frame(self.root)
		self.control_frame.pack(fill=tk.X, padx=10, pady=5)
		
		self.control_frame = tk.Frame(self.root)
		self.control_frame.pack(fill=tk.X, padx=10, pady=5)
		self.run_button = tk.Button(self.control_frame, text=" Run ", width=20, command=self.start_tests_thread)
		self.run_button.pack(side=tk.RIGHT, padx=10)
		self.hold_button = tk.Button(self.control_frame, text=" Hold ", width=20, command=self.toggle_hold, state=tk.DISABLED)
		self.hold_button.pack(side=tk.RIGHT, padx=10)
		self.cancel_button = tk.Button(self.control_frame, text=" Cancel ", width=20, command=self.cancel_tests, state=tk.DISABLED)
		self.cancel_button.pack(side=tk.RIGHT, padx=10)
		self.saveas_button = tk.Button(self.control_frame, text=" Save JSON ", width=20, command=self.save_config, state=tk.DISABLED)
		self.saveas_button.pack(side=tk.LEFT, padx=10)

	def open_settings_window(self):
		SettingsWindow(self.root, self.S2T_CONFIG, self.update_configuration)

	def update_configuration(self, updated_config):
		
		self.S2T_CONFIG = updated_config
		print("Configuration updated:", self.S2T_CONFIG)

	def load_experiments_file(self):
		file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("JSON files", "*.json")])
		if file_path:
			self.file_entry.delete(0, tk.END)
			self.file_entry.insert(0, file_path)
			self.load_experiments(file_path)
	
	def load_experiments(self, file_path):
		#try:
		
		self.experiments = OpenExperiment(file_path) if self.Framework == None else self.Framework.Recipes(file_path)
		self.saveas_button.configure(state=tk.NORMAL)

		self.create_experiment_rows()

		#except Exception as e:
		#    messagebox.showerror("Error", f"Failed to load experiments: {e}")
	
	def create_experiment_rows(self):
		for frame in self.experiment_frames:
			frame[0].destroy()
		self.experiment_frames.clear()
		
		for experiment_name, experiment_data in self.experiments.items():
			data = experiment_data
			#for data in experiment_data:
			frame = tk.Frame(self.experiment_container)
			frame.pack(fill=tk.X, pady=2)
			enabled_status = True if data.get('Experiment', "Disabled").lower() == 'enabled' else False
			enabled_var = tk.BooleanVar(value=enabled_status)
			tk.Checkbutton(frame, variable=enabled_var, command=lambda f=frame, v=enabled_var: self.toggle_experiment(f, v)).pack(side=tk.LEFT)
				
			tk.Label(frame, text=experiment_name, width=15).pack(side=tk.LEFT)
			tk.Label(frame, text=data.get('Test Name', ''), width=50).pack(side=tk.LEFT)
			tk.Label(frame, text=data.get('Test Mode', ''), width=15).pack(side=tk.LEFT)
			tk.Label(frame, text=data.get('Test Type', ''), width=15).pack(side=tk.LEFT)
				
			tk.Button(frame, text="Edit", command=lambda d=data: self.edit_experiment(d)).pack(side=tk.LEFT, padx=10)
				
			run_label = tk.Label(frame, text="Idle", bg="white", fg="black", width=10, relief=tk.GROOVE, borderwidth=1)
			run_label.pack(side=tk.LEFT, padx=10)
				
			self.experiment_frames.append((frame, run_label, enabled_var, data))
			self.toggle_experiment(frame, enabled_var)

	def toggle_experiment(self, frame, enabled_var):
		state = tk.NORMAL if enabled_var.get() else tk.DISABLED
		for widget in frame.winfo_children():
			if widget != frame.winfo_children()[0]:  # Skip the Checkbutton
				widget.configure(state=state)
	
	def edit_experiment(self, data):
		EditExperimentWindow(self.root, data, self.update_experiment)

	def update_experiment(self, updated_data):
		# Update the experiment data and refresh the display
		for frame, run_label, enabled_var, data in self.experiment_frames:
			if data == updated_data:
				# Update the display with new data
				enabled_status = updated_data.get('Experiment', "Disabled").lower() == 'enabled'
				enabled_var.set(enabled_status)
				#frame.winfo_children()[1].configure(text=updated_data.get('Test Name', ''))
				frame.winfo_children()[2].configure(text=updated_data.get('Test Name', ''))
				frame.winfo_children()[3].configure(text=updated_data.get('Test Mode', ''))
				frame.winfo_children()[4].configure(text=updated_data.get('Test Type', ''))
				break

	def test_ttl(self, ):
		#self.Framework.Test_Macros(self.root, self.experiments)
		TestTTLWindow(self.root, self.experiments, self.Framework)
		#EditExperimentWindow(self.root, data)
		#pass

	def start_tests_thread(self):
		self.cancel_requested.clear()
		# Clears Exceptions Queue
		while not self.exception_queue.empty():
			self.exception_queue.get()
			print(self.exception_queue)

		# Clear status label
		self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")

		# Reset run labels
		if not self.hold_active: 
			self.current_experiment_index = 0
			
			for _, run_label, _, _ in self.experiment_frames:
				run_label.configure(text="Idle", bg="white", fg="black")

		# Disable Run button and enable Cancel and Hold buttons
		self.run_button.configure(state=tk.DISABLED)
		self.cancel_button.configure(state=tk.NORMAL)
		self.hold_button.configure(state=tk.NORMAL)
		
			
		self.test_thread = threading.Thread(target=self.start_tests)
		self.test_thread.start()

	def start_tests(self):
		# Clears index if not is not active
		self.hold_active = False
		self.hold_button.configure(bg="SystemButtonFace")  # Reset hold button color
		self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")


		for index in range(self.current_experiment_index, len(self.experiment_frames)):
			frame, run_label, enabled_var, data = self.experiment_frames[index]
			success = False

			fail_on_loop = 2
			if index == fail_on_loop:
				sim_fail = True
			else: sim_fail = False
			
			if self.cancel_requested.is_set():
				run_label.configure(text="Cancelled", bg="gray", fg="black")
				self.cancel_requested.clear()
				self.status_label.configure(text=" Ready ", bg="white", fg="black")
				break
		   
			if enabled_var.get():
				test_mode = data.get('Test Type', '')
				run_label.configure(text="In Progress", bg="#00008B", fg="white")
				self.root.update_idletasks()

				try:
					if self.Framework == None:
						
						success = execute(task_name = test_mode, target_func=TestLogic2, exceptions = self.exception_queue, cancel_flag = self.cancel_requested, args =(test_mode, sim_fail), use_process = use_process)
					else:
						
						success = execute(task_name = test_mode, target_func=Framework_call, exceptions = self.exception_queue, cancel_flag = self.cancel_requested, args =(self.Framework, data, self.S2T_CONFIG), use_process = use_process)

				except TaskCancelledException as e:
					print("Task Cancelled by User --> Exception:", e)
					run_label.configure(text="Cancelled", bg="gray", fg="white")
					self.status_label.configure(text=" Ready ", bg="white", fg="black")
					self.cancel_requested.clear()
					#sys.exit()
					break

				except InterruptedError as e:
					print("Task Cancelled by User --> Exception:", e)
					run_label.configure(text="Cancelled", bg="gray", fg="white")
					self.status_label.configure(text=" Ready ", bg="white", fg="black")
					self.cancel_requested.clear()
					#sys.exit()
					break

				except Exception as e:
					print(e)
					run_label.configure(text="Fail", bg="yellow", fg="black")
					if self.stop_on_fail_var.get():
						break

				# Check for exceptions from threads
				if check_exceptions(self.exception_queue):
					#self.cancel_requested.set()
					run_label.configure(text="Cancelled", bg="gray", fg="white")
					self.status_label.configure(text=" Ready ", bg="white", fg="black")
					#sys.exit()
					break				

				if success:	
					print(f'Framework Control -- {test_mode.upper()} Completed --')
					run_label.configure(text="Done", bg="#006400", fg="white")
				else:					
					print(f'Framework Control -- {test_mode.upper()} Failed --')
					run_label.configure(text="Fail", bg="yellow", fg="black")
					if self.stop_on_fail_var.get():
						break

				if self.hold_active:
					self.current_experiment_index = index + 1
					self.status_label.configure(text=" Halted ", bg="yellow", fg="black")
					break
				
				self.current_experiment_index = index + 1
			else:
				self.current_experiment_index = index + 1
	
		# If all tests are completed
		if not self.hold_active and self.current_experiment_index >= len(self.experiment_frames):
			self.status_label.configure(text=" Completed ", bg="#006400", fg="white")

		# Enable Run button and disable Cancel and Hold buttons
		self.run_button.configure(state=tk.NORMAL)
		self.cancel_button.configure(state=tk.DISABLED)
		self.hold_button.configure(state=tk.DISABLED)

	def toggle_hold(self):
		self.hold_active = not self.hold_active
		if self.hold_active:
			self.hold_button.configure(bg="orange")
		else:
			self.hold_button.configure(bg="SystemButtonFace")
	
	def hold_tests(self):
		# Implement the logic to hold tests
		pass
	
	def cancel_tests(self):
		self.cancel_requested.set()
		self.current_experiment_index = 0
		self.status_label.configure(text=" Cancelling ", bg="#BF0000", fg="white")
		print("Cancelling current experiment, please wait...")  # Reset index on cancel
		#if self.test_thread and self.test_thread.is_alive():
		#	self.test_thread.join()  # Wait for the thread to finish

	def save_config(self):
		# Open a dialog to select the save location
		file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
		if file_path:
			Convert_xlsx_to_json(file_path, self.experiments)

class SettingsWindow:
	def __init__(self, parent, config, update_callback):
		self.top = tk.Toplevel(parent)
		self.top.title("Settings")
		
		self.config = config
		self.entries = {}
		self.update_callback = update_callback

		self.create_widgets()

	def create_widgets(self):
		row = 0
		for label, key in CONFIG_LABELS.items():
			tk.Label(self.top, text=label).grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
			entry = tk.Entry(self.top, width=20)
			entry.grid(row=row, column=1, padx=10, pady=5)
			# Display hex values for specific keys
			if key in ['AFTER_MRC_POST', 'EFI_POST', 'LINUX_POST']:
				entry.insert(0, f"{self.config[key]:#0x}")
			else:
				entry.insert(0, str(self.config[key]))
			self.entries[key] = entry
			row += 1
		tk.Button(self.top, text="Save", command=self.save_changes).grid(row=row, column=0, columnspan=2, pady=10)

	def save_changes(self):
		for key, entry in self.entries.items():
			try:
				# Convert hex input for specific keys
				if key in ['AFTER_MRC_POST', 'EFI_POST', 'LINUX_POST']:
					self.config[key] = int(entry.get(), 16)
				else:
					self.config[key] = int(entry.get())
			except ValueError:
				messagebox.showerror("Invalid Input", f"Invalid value for {key}. Please enter a valid integer.")
				return
		self.update_callback(self.config)
		self.top.destroy()
		
class EditExperimentWindow:
	def __init__(self, parent, data, update_callback):
		self.top = tk.Toplevel(parent)
		self.top.title("Edit Experiment")
		
		self.data = data
		self.entries = {}
		self.update_callback = update_callback
		self.original_types = {key: type(value) for key, value in data.items()}

		# Create a canvas and a scrollbar
		self.canvas = tk.Canvas(self.top)
		self.scrollbar = tk.Scrollbar(self.top, orient="vertical", command=self.canvas.yview)
		self.scrollable_frame = tk.Frame(self.canvas)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(
				scrollregion=self.canvas.bbox("all")
			)
		)

		self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=800)
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.scrollbar.pack(side="right", fill="y")
		self.canvas.pack(side="left", fill="both", expand=True)


		self.create_widgets()
	
	def create_widgets(self):
		row = 0
		for key, value in self.data.items():
			
			tk.Label(self.scrollable_frame, text=key).grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
			entry = tk.Entry(self.scrollable_frame, width=100)
			entry.grid(row=row, column=1, columnspan=3, padx=10, pady=5)
			entry.insert(0, str(value) if value is not None else '')
			self.entries[key] = entry
			row += 1
		tk.Button(self.scrollable_frame, text="Save", command=self.save_changes).grid(row=row, column=0, columnspan=2, pady=10)

	
	def save_changes(self):
		for key, entry in self.entries.items():
			original_type = self.original_types[key]
			self.data[key] = self.convert_type(entry.get(), original_type) #if entry.get() != '' else None
		#for key, entry in self.entries.items():
		#	self.data[key] = entry.get() if entry.get() != '' else None
		self.update_callback(self.data)
		self.top.destroy()   

	def convert_type(self, value, original_type):
		if value == ''  or value == 'None':
			return None
		try:
			if original_type is bool:
				return value.lower() in ('true', '1', 'yes')
			return original_type(value)
		except ValueError:
			return value

class TestTTLWindow:
	def __init__(self, parent, experiments, test_function=None):
		self.top = tk.Toplevel(parent)
		self.top.title("Teraterm Macros Tester (TTL)")
		self.experiments = experiments
		self.test_function = test_function
		self.stop_event = threading.Event()
		self.test_thread = None
		self.exception_queue = queue.Queue()
		self.selected_experiment_name = tk.StringVar()
		self.selected_experiment_name.set(next(iter(experiments)))  # Set default to the first experiment

		self.create_widgets()
		self.update_experiment_info()
		
		# Bind the window close event
		self.top.protocol("WM_DELETE_WINDOW", self.on_close)
	
	def create_widgets(self):
		# Row 1: Select Experiment, Experiment Menu, and Test Button
		tk.Label(self.top, text="Select Experiment", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)

		self.experiment_menu = tk.OptionMenu(self.top, self.selected_experiment_name, *self.experiments.keys(), command=self.update_experiment_info)
		self.experiment_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

		tk.Button(self.top, text=" Test Macro ", command=self.start_test_thread).grid(row=0, column=2, padx=5, pady=5, sticky=tk.EW)
		tk.Button(self.top, text=" Cancel", command=self.cancel_test).grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

		# Row 2: Separator Line
		separator = tk.Frame(self.top, height=2, bd=1, relief=tk.SUNKEN)
		separator.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

		# Row 3: Visual and Content
		self.visual_label = tk.Label(self.top, text="Visual: ")
		self.visual_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

		self.content_label = tk.Label(self.top, text="Content: ")
		self.content_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

		tk.Button(self.top, text=" Reboot Unit ", command=self.reboot_unit).grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)

		# Row 4: TTL Path
		self.ttl_path_label = tk.Label(self.top, text="TTL Folder: ")
		self.ttl_path_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

		# Row 5: Commands List and Open/Edit TTL Button
		self.ttl_files_listbox = tk.Listbox(self.top)
		self.ttl_files_listbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)

		tk.Button(self.top, text=" Open TTL ", command=self.open_edit_ttl_file).grid(row=4, column=2, padx=5, pady=5, sticky=tk.EW)

	def update_experiment_info(self, *args):
		selected_experiment = self.experiments[self.selected_experiment_name.get()]

		self.visual = selected_experiment.get('Visual ID', None)
		self.content = selected_experiment.get('Content', None)
		self.ttl_path = selected_experiment.get('TTL Folder', None)
		self.tnumber = selected_experiment.get('Test Number', 1)
		self.ttime = selected_experiment.get('Test Time', 30)
		self.bucket = selected_experiment.get('Bucket', 'dummy')
		self.passstring = selected_experiment.get('Pass String', 'Test Complete')
		self.failstring = selected_experiment.get('Fail String', 'Test Failed')

		# Update labels with selected values
		self.visual_label.config(text=f"Visual: {self.visual}")
		self.content_label.config(text=f"Content: {self.content}")
		self.ttl_path_label.config(text=f"TTL Folder: {self.ttl_path}")

		# List .ttl files in the TTL Path
		self.ttl_files_listbox.delete(0, tk.END)  # Clear previous entries
		if self.ttl_path and os.path.isdir(self.ttl_path):
			ttl_files = [f for f in os.listdir(self.ttl_path) if f.endswith('.ttl')]
			for ttl_file in ttl_files:
				self.ttl_files_listbox.insert(tk.END, ttl_file)

	def start_test_thread(self):
		# Stop any existing thread
		self.stop_event.set()
		task_name = 'TTL_Check'
		if self.test_thread and self.test_thread.is_alive():
			self.test_thread.stop()
			self.test_thread.join()

		# Clear the stop event and start a new thread
		self.stop_event.clear()
		self.test_thread = ThreadHandler(target=self.run_test, name=f'Thread-{task_name}', args=())
		self.test_thread.start()

	def run_test(self, *args):
		visual = self.visual
		cmds = self.ttl_path
		ttime = self.ttime
		tnumber = self.tnumber
		bucket = self.bucket

		try:	
			
			execute(task_name = 'TTL Test',target_func = TTL_testing, exceptions=self.exception_queue, cancel_flag = self.stop_event, args=(self.test_function, visual, cmds, bucket, ttime, tnumber), use_process = use_process )

		except TaskCancelledException as e:
			print('TTL Test Cancelled by User')
		except Exception as e:
			print('Exception raised: ', e)  # Remove this break if you want the test to run continuously

	def reboot_unit(self):
		self.test_function.reboot_unit(waittime=60, u600w=False)

	def open_edit_ttl_file(self):
		selected_index = self.ttl_files_listbox.curselection()
		if selected_index:
			selected_file = self.ttl_files_listbox.get(selected_index)
			ttl_path = self.ttl_path#_label.cget("text").replace("TTL Path: ", "")
			file_path = os.path.join(ttl_path, selected_file)
			if os.path.isfile(file_path):
				os.startfile(file_path)  # Open the file with the default text editor

	def on_close(self):
		# Stop the thread and close the window
		self.stop_event.set()
		self.top.destroy()

	def cancel_test(self):
		self.stop_event.set()
		if self.test_thread and self.test_thread.is_alive():
			self.test_thread.stop()
			self.test_thread.join()
	#def test_function(self):#self, visual, bucket, ttl_path, test='Dummy', ttime=30, tnum=1):
	#	print('add test function')
		#print(f"Running test with visual={visual}, bucket={bucket}, ttl_path={ttl_path}, test={test}, ttime={ttime}, tnum={tnum}")
		# Implement the actual test logic here

## Placeholder for a context manager, not being used for now
@contextmanager
def managed_thread(target, args=(), kwargs=None):
	thread = ThreadHandler(target=target, args=args, kwargs=kwargs)
	try:
		thread.start()
		yield thread
	finally:
		thread.stop()
		thread.join()

def check_exceptions(exception_queue):
	while not exception_queue.empty():
		exception = exception_queue.get()
		if isinstance(exception, TaskCancelledException):
			print("Task cancelled, stopping all executions.")
			return True
	return False

# Function to monitor execution variables -- yet to be enabled, code is not final...
def monitor_task(cancel_flag, task_name,exception_queue):

	try:
		while not cancel_flag.is_set():
			time.sleep(1)
			
		print('Cancelling now betch!!')
		
		raise TaskCancelledException(f"{task_name} cancelled")
			# Check periodically
		
	except:
		exception_queue.put(TaskCancelledException(f"{task_name} cancelled"))	
	
def monitor(cancel_flag, task_name, execution_thread):

	while execution_thread.is_alive():
		if cancel_flag.is_set():
			time.sleep(1)  # Check periodically
		if not execution_thread.is_alive():
			return 
	
	print('Cancelling now')
	execution_thread.join()
	print('Cancelling now')
	#exception_queue.put(TaskCancelledException(f"{task_name} cancelled"))
	raise TaskCancelledException(f"{task_name} cancelled")

# Offline UI Test functions 
def TestLogic(txt, cancel_flag, exception_queue):
	try:
		for i in range(10):
			if cancel_flag.is_set():
				print('Cancelling TestLogic')
				exception_queue.put(TaskCancelledException(f"{txt} logic cancelled"))
				raise TaskCancelledException(f"{txt} logic cancelled")
			print(f'Testing {txt} Logic count:{i}')
			time.sleep(1)
		print('Done')
	except TaskCancelledException as e:
		exception_queue.put(e)

def TestLogic2(txt, simulate_fail, exception_queue, cancel_flag):
	
	
	try:
		for i in range(10):
			cancel = cancel_flag.is_set() if cancel_flag != None else False
			print(f'Testing {txt} Logic count:{i} -- {cancel} :: {cancel_flag}')
			if cancel or (i == 5 and simulate_fail): 
				raise InterruptedError('SimulatedFailure')
			time.sleep(1)
		print('Done')
	except InterruptedError as e:
		print(f"Logic Interrupted by user: {e}")
		exception_queue.put(e)  # Put the exception into the queue

	except TaskCancelledException as e:
		print(f"Exception in TestLogic2: {e}")
		exception_queue.put(e)  # Put the exception into the queue

def TTL_testing(test_function, visual, cmds, bucket, ttime, tnumber, exception_queue, cancel_flag):
	cancel = cancel_flag.is_set() if cancel_flag != None else False
	try:
		if test_function == None:
			print('add test function')
			for i in range(1,5):
				print(i)
				time.sleep(1)
			if i > 5 and cancel: raise InterruptedError('User SimulatedError')
			for i in range(5,10):
				print(i)
				time.sleep(1)
		
		else:
			test_function.TTL_Test(visual, cmds, bucket = bucket, test = 'TTL_Macro_Validation', ttime=ttime, tnum=tnumber, cancel_flag=cancel_flag)
	
	except InterruptedError as e:
		print(f"Framework Iteration Interrupted: {e}")
		exception_queue.put(e)
	except TaskCancelledException as e:
		print(f"User Interruption in TTL_testing: {e}")
		exception_queue.put(e)
	except Exception as e:
		print(f"Exception in TTL_testing: {e}")
		exception_queue.put(e)  # Put the exception into the queue
			
def Framework_call(Framework, data, S2TCONFIG, exception_queue, cancel_flag):
	try:
		
		Framework.RecipeExecutor(data=data, S2T_BOOT_CONFIG = S2TCONFIG, cancel_flag=cancel_flag)
	
	except InterruptedError as e:
		print(f"Framework Iteration Interrupted: {e}")
		exception_queue.put(e)
	except Exception as e:
		print(f"Exception during Framework Execution: {e}")
		exception_queue.put(e)  # Put the exception into the queue

# Executes threads or process for Framework Flow
def execute(task_name, target_func, exceptions, cancel_flag, args, use_process=True):
	#target_func = TestLogic2 if Framework is None else Framework_call
	#args = (task_name,) if Framework is None else (Framework, data)

	try:
		if use_process:
			exception_queue = multiprocessing.Queue()
			
			handler = multiprocessing.Process(target=target_func, args=args + (exception_queue,None))
		else:
			exception_queue = exceptions
			handler = ThreadHandler(target=target_func, name=f'Thread-{task_name}', args=args + (exception_queue, cancel_flag))
		
		handler.start()
		print(f"Framework Control -- Starting new process task: {task_name} -- ")
		
		while not cancel_flag.is_set():
			time.sleep(1)
			if not handler.is_alive():
				break
		
		#print('Moving forward')
		if cancel_flag.is_set():
			#print('FlagRaised')
			#handler.terminate() if use_process else handler.stop()
			raise TaskCancelledException(f"{task_name} cancelled by User")
		
		handler.terminate() if use_process else handler.stop()
		handler.join()

		# Check for exceptions in the queue
		if not exception_queue.empty():
			exception = exception_queue.get()
			print(f"Exception occurred during {task_name}: {exception}")
			return False  # Indicate failure

		return True  # Indicate success

	except InterruptedError as e:
		print(f"Framework Iteration Interrupted: {e}")
		exceptions.put(e)

	except TaskCancelledException as e:
		print(f"{task_name} Main Thread Execution Cancelled -- Exception {e}")
		exceptions.put(e)
		handler.terminate() if use_process else handler.stop()
		#handler.join()
		return False

	except Exception as e:
		print(f"Exception occurred during {task_name}: {e}")
		#cancel_flag.set()
		handler.terminate() if use_process else handler.stop()
		handler.join()
		exceptions.put(e)
		return False  # Indicate failure

def OpenExperiment(path):
	# Placeholder for the actual implementation
	# Assume fh.process_excel_file and fh.create_tabulated_format are defined elsewhere

	if path.endswith('.json'):
		data_from_sheets = fh.load_json_file(path)
		#tabulated_df = data_from_sheets
	elif path.endswith('.xlsx'):
		data_from_sheets = fh.process_excel_file(path)
		# Create the tabulated format
	else: return None

	return data_from_sheets

def Convert_xlsx_to_json(file_path, experiments):
	data_from_json = fh.save_excel_to_json(file_path, experiments)
	return data_from_json

def run(Framework):
	root = tk.Tk()
	app = DebugFrameworkControlPanel(root,Framework)
	root.mainloop()

if __name__ == "__main__":
	Framework = None
	root = tk.Tk()
	app = DebugFrameworkControlPanel(root, Framework)
	root.mainloop()
