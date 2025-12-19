import sys
import os
# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xlwings as xw

try:
    from .PPVLoopChecks import PTCReportGUI
    from .PPVDataChecks import PPVReportGUI
    from ..api.dpmb import dpmbGUI
    from .PPVFileHandler import FileHandlerGUI
    from .PPVFrameworkReport import FrameworkReportBuilder
    from .AutomationDesigner import start_automation_flow_designer
    from .ExperimentBuilder import ExperimentBuilderGUI
    from .MCADecoder import MCADecoderGUI
except ImportError:
    from gui.PPVLoopChecks import PTCReportGUI
    from gui.PPVDataChecks import PPVReportGUI
    from api.dpmb import dpmbGUI
    from gui.PPVFileHandler import FileHandlerGUI
    from gui.PPVFrameworkReport import FrameworkReportBuilder
    from gui.AutomationDesigner import start_automation_flow_designer
    from gui.ExperimentBuilder import ExperimentBuilderGUI
    from gui.MCADecoder import MCADecoderGUI
#import pyfiglet

def display_banner():
    # Create the banner text
    banner_text = rf'''
=============================================================================
    ____  ____  __  ___   ____  ____ _    __   __________  ____  __   _____
   / __ \/ __ \/  |/  /  / __ \/ __ \ |  / /  /_  __/ __ \/ __ \/ /  / ___/
  / / / / /_/ / /|_/ /  / /_/ / /_/ / | / /    / / / / / / / / / /   \__ \
 / /_/ / ____/ /  / /  / ____/ ____/| |/ /    / / / /_/ / /_/ / /______/ /
/_____/_/   /_/  /_/  /_/   /_/     |___/    /_/  \____/\____/_____/____/

=============================================================================
    '''

    # Print the banner
    print(banner_text)

# Create the main window
class Tools(tk.Frame):
	def __init__(self, root, default_product="GNR"):
		super().__init__(root)
		self.root = root
		self.default_product = default_product  # Store default product selection
		self.root.title("PPV Tools Hub")

		# Enable full-screen resizing
		self.root.state('zoomed')  # Maximize window on Windows
		self.root.rowconfigure(0, weight=1)
		self.root.columnconfigure(0, weight=1)

		# Configure styles
		self.setup_styles()

		# Main container
		main_container = tk.Frame(self.root, bg='#f0f0f0')
		main_container.grid(row=0, column=0, sticky="nsew")
		main_container.rowconfigure(0, weight=1)
		main_container.columnconfigure(0, weight=1)

		# Create canvas with scrollbar for the tool cards
		canvas = tk.Canvas(main_container, bg='#f0f0f0', highlightthickness=0)
		scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
		self.scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
		)

		canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)

		canvas.grid(row=0, column=0, sticky="nsew")
		scrollbar.grid(row=0, column=1, sticky="ns")

		# Title section
		title_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', pady=20)
		title_frame.pack(fill="x", padx=20, pady=(20, 10))

		title_label = tk.Label(title_frame, text="PPV TOOLS HUB",
							   font=("Segoe UI", 24, "bold"),
							   bg='#2c3e50', fg='white')
		title_label.pack()

		subtitle_label = tk.Label(title_frame,
								 text="Comprehensive Suite for PPV Data Analysis & Management",
								 font=("Segoe UI", 11),
								 bg='#2c3e50', fg='#ecf0f1')
		subtitle_label.pack()

		# Product indicator
		product_indicator_frame = tk.Frame(title_frame, bg='#34495e', padx=15, pady=8)
		product_indicator_frame.pack(pady=(10, 0))

		product_names = {
			'GNR': 'Granite Rapids',
			'CWF': 'Clearwater Forest',
			'DMR': 'Diamond Rapids'
		}
		
		product_full_name = product_names.get(self.default_product, self.default_product)
		
		product_indicator = tk.Label(
			product_indicator_frame,
			text=f"📌 Default Product: {self.default_product} ({product_full_name})",
			font=("Segoe UI", 9),
			bg='#34495e',
			fg='#ecf0f1'
		)
		product_indicator.pack()

		# Tools grid container
		tools_container = tk.Frame(self.scrollable_frame, bg='#f0f0f0')
		tools_container.pack(fill="both", expand=True, padx=20, pady=10)

		# Configure grid columns for responsive layout
		tools_container.columnconfigure(0, weight=1)
		tools_container.columnconfigure(1, weight=1)

		# Create tool cards
		self.create_tool_card(tools_container, 0, 0,
			"PTC Loop Parser",
			"Parse logs from PTC experiment data and generate DPMB report format files.",
			"• Automated log parsing\n• DPMB format output\n• Batch processing support",
			"#3498db",
			self.open_ppv_loop_parser)

		self.create_tool_card(tools_container, 0, 1,
			"PPV MCA Report",
			"Generate comprehensive MCA reports from Bucketer files or S2T Logger data.",
			"• Bucketer file analysis\n• S2T Logger integration\n• MCA decoding & visualization",
			"#e74c3c",
			self.open_ppv_mca_report)

		self.create_tool_card(tools_container, 1, 0,
			"MCA Single Decoder",
			"Decode individual MCA registers for CHA, LLC, CORE, MEMORY, IO, and First Error.",
			"• Single register decode\n• Multi-product support\n• Easy copy/paste results",
			"#e74c3c",
			self.open_mca_decoder)

		self.create_tool_card(tools_container, 1, 1,
			"DPMB Requests",
			"Interface for Bucketer data requests through DPMB API.",
			"• Direct API connection\n• Automated data retrieval\n• Custom query builder",
			"#9b59b6",
			self.open_dpmb)

		self.create_tool_card(tools_container, 2, 0,
			"File Handler",
			"Merge and manage multiple data files efficiently.",
			"• Merge DPMB format files\n• Append MCA reports\n• Batch file operations",
			"#f39c12",
			self.open_filehandler)

		self.create_tool_card(tools_container, 2, 1,
			"Framework Report Builder",
			"Create comprehensive reports from Debug Framework experiment data.",
			"• Unit overview generation\n• Summary file merging\n• Multi-experiment analysis",
			"#1abc9c",
			self.open_frameworkreport)

		self.create_tool_card(tools_container, 3, 0,
			"Automation Flow Designer",
			"Visual tool for designing and managing automation test flows.",
			"• Drag-and-drop flow design\n• Experiment sequencing\n• Export automation configs",
			"#16a085",
			self.open_automation_designer)

		self.create_tool_card(tools_container, 3, 1,
			"Experiment Builder",
			"Create and edit JSON configurations for Debug Framework Control Panel.",
			"• Build experiments from scratch\n• Import from Excel/JSON\n• Export Control Panel configs",
			"#1abc9c",
			self.open_experiment_builder)

		# Footer with close button
		footer_frame = tk.Frame(self.scrollable_frame, bg='#f0f0f0', pady=20)
		footer_frame.pack(fill="x", padx=20)

		exit_button = tk.Button(footer_frame, text="Close Application",
							   command=self.root.quit,
							   bg="#e74c3c", fg="white",
							   font=("Segoe UI", 10, "bold"),
							   padx=30, pady=10,
							   relief=tk.FLAT,
							   cursor="hand2")
		exit_button.pack()

		# Bind mouse wheel to canvas
		canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

	def setup_styles(self):
		"""Configure ttk styles for consistent appearance"""
		style = ttk.Style()
		style.theme_use('clam')

	def create_tool_card(self, parent, row, col, title, description, features, color, command, colspan=1):
		"""Create a modern card-style button for each tool"""
		card = tk.Frame(parent, bg='white', relief=tk.FLAT, borderwidth=2)
		card.grid(row=row, column=col, columnspan=colspan, padx=10, pady=10, sticky="nsew")

		# Header with color accent (increased height)
		header = tk.Frame(card, bg=color, height=12)
		header.pack(fill="x")

		# Content area
		content = tk.Frame(card, bg='white', padx=20, pady=15)
		content.pack(fill="both", expand=True)

		# Title
		title_label = tk.Label(content, text=title,
							  font=("Segoe UI", 14, "bold"),
							  bg='white', fg='#2c3e50')
		title_label.pack(anchor="w", pady=(0, 5))

		# Description
		desc_label = tk.Label(content, text=description,
							 font=("Segoe UI", 9),
							 bg='white', fg='#7f8c8d',
							 wraplength=350, justify="left")
		desc_label.pack(anchor="w", pady=(0, 10))

		# Features
		features_label = tk.Label(content, text=features,
								 font=("Segoe UI", 9),
								 bg='white', fg='#34495e',
								 justify="left")
		features_label.pack(anchor="w", pady=(0, 15))

		# Launch button
		launch_btn = tk.Button(content, text="Launch Tool →",
							  command=command,
							  bg=color, fg='white',
							  font=("Segoe UI", 9, "bold"),
							  padx=20, pady=8,
							  relief=tk.FLAT,
							  cursor="hand2")
		launch_btn.pack(anchor="w")

		# Hover effects - only bind to card to prevent event conflicts
		hover_active = [False]  # Use list to allow modification in nested functions

		def on_enter(e):
			if not hover_active[0]:
				hover_active[0] = True
				card.config(bg='#e8e8e8')
				content.config(bg='#e8e8e8')
				title_label.config(bg='#e8e8e8')
				desc_label.config(bg='#e8e8e8')
				features_label.config(bg='#e8e8e8')
				launch_btn.config(bg=self.adjust_color(color, -20))

		def on_leave(e):
			# Only trigger if mouse actually leaves the card
			if hover_active[0]:
				x, y = e.x_root, e.y_root
				card_x = card.winfo_rootx()
				card_y = card.winfo_rooty()
				card_w = card.winfo_width()
				card_h = card.winfo_height()

				# Check if mouse is outside card boundaries
				if x < card_x or x > card_x + card_w or y < card_y or y > card_y + card_h:
					hover_active[0] = False
					card.config(bg='white')
					content.config(bg='white')
					title_label.config(bg='white')
					desc_label.config(bg='white')
					features_label.config(bg='white')
					launch_btn.config(bg=color)

		# Bind only to the card frame
		card.bind("<Enter>", on_enter)
		card.bind("<Leave>", on_leave)

		# Make all widgets clickable but don't bind hover events to them
		for widget in [card, content, header, title_label, desc_label, features_label]:
			widget.bind("<Button-1>", lambda e, cmd=command: cmd())
			widget.config(cursor="hand2")

	def adjust_color(self, hex_color, amount):
		"""Adjust color brightness for hover effects"""
		hex_color = hex_color.lstrip('#')
		rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
		rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
		return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

	def add_separator(self, parent, row):
		separator = ttk.Separator(parent, orient='horizontal')
		separator.grid(row=row, columnspan=2, sticky="ew", pady=5)

	def open_ppv_loop_parser(self):
		"""Open PTC Loop Parser tool"""
		root1 = tk.Toplevel(self.root)
		root1.title('PPV Loop Parser')
		app1 = PTCReportGUI(root1, default_product=self.default_product)
		self.center_window(root1)

	def open_ppv_mca_report(self):
		"""Open PPV MCA Report tool"""
		root2 = tk.Toplevel(self.root)
		root2.title('PPV MCA Report')
		app2 = PPVReportGUI(root2, default_product=self.default_product)
		self.center_window(root2)

	def open_dpmb(self):
		"""Open DPMB Requests tool"""
		root3 = tk.Toplevel(self.root)
		root3.title('DPMB Bucketer Requests')
		app3 = dpmbGUI(root3, default_product=self.default_product)
		self.center_window(root3)

	def open_filehandler(self):
		"""Open File Handler tool"""
		root4 = tk.Toplevel(self.root)
		root4.title('File Handler')
		app4 = FileHandlerGUI(root4, default_product=self.default_product)
		self.center_window(root4)

	def open_frameworkreport(self):
		"""Open Framework Report Builder tool"""
		root5 = tk.Toplevel(self.root)
		root5.title('Framework Report Builder')
		app5 = FrameworkReportBuilder(root5, default_product=self.default_product)
		# Framework report is already maximized, no need to center

	def open_automation_designer(self):
		"""Open Automation Flow Designer tool"""
		start_automation_flow_designer(parent=self.root, default_product=self.default_product)

	def open_experiment_builder(self):
		"""Open Experiment Builder tool"""
		ExperimentBuilderGUI(parent=self.root, default_product=self.default_product)

	def open_mca_decoder(self):
		"""Open MCA Single Decoder tool"""
		root6 = tk.Toplevel(self.root)
		root6.title('MCA Single Decoder')
		app6 = MCADecoderGUI(root6, default_product=self.default_product)
		self.center_window(root6)

	def center_window(self, window):
		"""Center a window on the screen"""
		window.update_idletasks()
		width = window.winfo_width()
		height = window.winfo_height()
		x = (window.winfo_screenwidth() // 2) - (width // 2)
		y = (window.winfo_screenheight() // 2) - (height // 2)
		window.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
	from ProductSelector import show_product_selector
	
	display_banner()
	
	# Show product selector first
	selected_product = show_product_selector()
	
	# Exit if user cancelled
	if not selected_product:
		print("Product selection cancelled. Exiting...")
		import sys
		sys.exit(0)
	
	print(f"\nSelected Product: {selected_product}")
	print("Launching PPV Tools Hub...\n")
	
	root = tk.Tk(baseName='MainWindow')
	app = Tools(root, default_product=selected_product)
	#app.pack(fill='both', expand=True)
	root.mainloop()
