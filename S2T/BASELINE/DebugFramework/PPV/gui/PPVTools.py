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
    banner_text = r'''
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║  ████████╗██╗  ██╗██████╗     ██████╗ ███████╗██████╗ ██╗   ██╗ ██████╗    ║
║  ╚══██╔══╝██║  ██║██╔══██╗    ██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝    ║
║     ██║   ███████║██████╔╝    ██║  ██║█████╗  ██████╔╝██║   ██║██║  ███╗   ║
║     ██║   ██╔══██║██╔══██╗    ██║  ██║██╔══╝  ██╔══██╗██║   ██║██║   ██║   ║
║     ██║   ██║  ██║██║  ██║    ██████╔╝███████╗██████╔╝╚██████╔╝╚██████╔╝   ║
║     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝╚═════╝  ╚═════╝  ╚═════╝    ║
║                                                                            ║
║            ████████╗ ██████╗  ██████╗ ██╗     ███████╗                     ║
║            ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝                     ║
║               ██║   ██║   ██║██║   ██║██║     ███████╗                     ║
║               ██║   ██║   ██║██║   ██║██║     ╚════██║                     ║
║               ██║   ╚██████╔╝╚██████╔╝███████╗███████║                     ║
║               ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝                     ║
║                                                                            ║
║         Test Hole Resolution Debug Tools - Unit Characterization Suite     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    '''

    # Print the banner
    print(banner_text)

# Create the main window
class Tools(tk.Frame):
	def __init__(self, root, default_product="GNR"):
		super().__init__(root)
		self.root = root
		self.default_product = default_product  # Store default product selection
		self.root.title("THR Debug Tools Hub")

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

		title_label = tk.Label(title_frame, text="THR DEBUG TOOLS HUB",
							   font=("Segoe UI", 24, "bold"),
							   bg='#2c3e50', fg='white')
		title_label.pack()

		subtitle_label = tk.Label(title_frame,
								 text="Test Hole Resolution Debug Tools - Unit Characterization & Debug Flow Suite",
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

		# Debug Flow button in header
		flow_button = tk.Button(title_frame, text="📊 View Debug Flow",
							   command=self.show_debug_flow,
							   bg="#3498db", fg="white",
							   font=("Segoe UI", 9, "bold"),
							   padx=25, pady=8,
							   relief=tk.FLAT,
							   cursor="hand2")
		flow_button.pack(pady=(10, 0))

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

	def show_debug_flow(self):
		"""Display the recommended debug flow for using the tools suite"""
		flow_window = tk.Toplevel(self.root)
		flow_window.title("THR Debug Tools - Recommended Flow")
		flow_window.geometry("1100x550")
		flow_window.configure(bg='#e8e8e8')
		flow_window.resizable(True, True)  # Allow resizing if needed

		# Make it modal
		flow_window.transient(self.root)
		flow_window.grab_set()

		# Main container
		main_frame = tk.Frame(flow_window, bg='#e8e8e8')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

		# Title
		title_label = tk.Label(
			main_frame,
			text="🔄 Unit Characterization & Debug Flow",
			font=("Segoe UI", 16, "bold"),
			bg='#e8e8e8',
			fg='#1a1a1a'
		)
		title_label.pack(pady=(0, 2))

		subtitle_label = tk.Label(
			main_frame,
			text="From Factory Testing to Root Cause Analysis",
			font=("Segoe UI", 10),
			bg='#e8e8e8',
			fg='#2c3e50'
		)
		subtitle_label.pack(pady=(0, 8))

		# Flow container with grid layout
		flow_container = tk.Frame(main_frame, bg='#e8e8e8')
		flow_container.pack(fill="both", expand=True)

		# Configure grid - 5 columns (box, arrow, box, arrow, box)
		for i in range(5):
			if i % 2 == 0:  # Box columns
				flow_container.columnconfigure(i, weight=3, minsize=100)
			else:  # Arrow columns
				flow_container.columnconfigure(i, weight=0, minsize=25)

		# Configure grid rows - let content determine height
		for i in range(5):
			flow_container.rowconfigure(i, weight=0, minsize=0)

		# Row 1: Steps 1-3
		self.create_compact_flow_box(flow_container, "1", "Initial Data Query", "DPMB", "#9b59b6", row=0, col=0)
		self.create_horizontal_arrow(flow_container, row=0, col=1)
		self.create_compact_flow_box(flow_container, "2", "MCA Analysis", "MCA Report + Decoder", "#e74c3c", row=0, col=2)
		self.create_horizontal_arrow(flow_container, row=0, col=3)
		self.create_compact_flow_box(flow_container, "3", "Additional Analysis - PTC / PPV Validation runs", "PTC Parser", "#f39c12", row=0, col=4, optional=True)

		# Vertical arrow from Step 3 to Step 4
		self.create_vertical_arrow(flow_container, row=1, col=4)

		# Row 2: Steps 4-6
		self.create_compact_flow_box(flow_container, "4", "Experiment Design", "Builder + Flow Designer", "#1abc9c", row=2, col=4)
		self.create_horizontal_arrow(flow_container, row=2, col=3, reverse=True)
		self.create_compact_flow_box(flow_container, "5", "Framework Execution", "Debug Framework", "#3498db", row=2, col=2)
		self.create_horizontal_arrow(flow_container, row=2, col=1, reverse=True)
		self.create_compact_flow_box(flow_container, "6", "Results Analysis", "Report Builder + Files", "#16a085", row=2, col=0)

		# Vertical arrow from Step 6 to Step 7
		self.create_vertical_arrow(flow_container, row=3, col=0)

		# Row 3: Step 7 (left aligned)
		self.create_compact_flow_box(flow_container, "7", "Root Cause & Content", "Class Testing & Content", "#27ae60", row=4, col=0)

		# Bottom info
		info_frame = tk.Frame(main_frame, bg='#d4d4d4', relief=tk.SOLID, borderwidth=1)
		info_frame.pack(fill="x", pady=(8, 0))

		info_text = "💡 Systematic approach from data collection to root cause • Integrated toolset • Reduced debug time"
		info_label = tk.Label(
			info_frame,
			text=info_text,
			font=("Segoe UI", 9),
			bg='#d4d4d4',
			fg='#1a1a1a',
			wraplength=800,
			justify='center'
		)
		info_label.pack(pady=6, padx=10)

		# Close button
		close_btn = tk.Button(
			main_frame,
			text="Close",
			command=lambda: self.close_flow_window(flow_window),
			bg="#2c3e50",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			padx=40,
			pady=8,
			relief=tk.FLAT,
			cursor="hand2"
		)
		close_btn.pack(pady=6)

		# Center the window
		flow_window.update_idletasks()
		width = 1100
		height = 550
		x = (flow_window.winfo_screenwidth() // 2) - (width // 2)
		y = (flow_window.winfo_screenheight() // 2) - (height // 2)
		flow_window.geometry(f'{width}x{height}+{x}+{y}')

	def close_flow_window(self, window):
		"""Close flow window"""
		window.destroy()

	def create_compact_flow_box(self, parent, number, title, tool, color, row=0, col=0, optional=False):
		"""Create a compact visual flow box"""
		box = tk.Frame(parent, bg='#ffffff', relief=tk.SOLID, borderwidth=2,
					  highlightbackground=color, highlightthickness=3, width=220)
		box.grid(row=row, column=col, padx=2, pady=3, sticky="ew")
		box.grid_propagate(True)  # Allow box to resize to content

		# Colored bar
		tk.Frame(box, bg=color, height=1).pack(fill="x")

		# Content
		content = tk.Frame(box, bg='#ffffff', padx=10, pady=1)
		content.pack(fill="both", expand=True)

		# Badge
		badge_text = f"Step {number}" if not optional else f"Step {number} (Opt)"
		badge = tk.Label(
			content,
			text=badge_text,
			font=("Segoe UI", 7, "bold"),
			bg=color,
			fg='white',
			padx=6,
			pady=1
		)
		badge.pack(anchor="w", pady=0)

		# Title
		title_label = tk.Label(
			content,
			text=title,
			font=("Segoe UI", 9, "bold"),
			bg='#ffffff',
			fg='#1a1a1a',
			wraplength=190,
			justify='left'
		)
		title_label.pack(anchor="w", pady=0)

		# Tool
		tool_label = tk.Label(
			content,
			text=f"🔧 {tool}",
			font=("Segoe UI", 8, "italic"),
			bg='#ffffff',
			fg='#2c3e50',
			wraplength=190,
			justify='left'
		)
		tool_label.pack(anchor="w")

	def create_horizontal_arrow(self, parent, row=0, col=0, reverse=False):
		"""Create a horizontal arrow between steps"""
		arrow_frame = tk.Frame(parent, bg='#e8e8e8')
		arrow_frame.grid(row=row, column=col, padx=2, pady=2)

		canvas = tk.Canvas(arrow_frame, bg='#e8e8e8', width=50, height=20, highlightthickness=0)
		canvas.pack()

		def draw(event=None):
			canvas.delete("all")
			w = canvas.winfo_width()
			h = canvas.winfo_height()
			if w > 10 and h > 10:
				center_y = h // 2
				if reverse:
					# Left-pointing arrow
					canvas.create_line(w-5, center_y, 5, center_y, fill='#5a5a5a', width=3, arrow=tk.LAST, arrowshape=(10, 12, 5))
				else:
					# Right-pointing arrow
					canvas.create_line(5, center_y, w-5, center_y, fill='#5a5a5a', width=3, arrow=tk.LAST, arrowshape=(10, 12, 5))

		canvas.bind('<Configure>', draw)
		arrow_frame.after(100, draw)

	def create_vertical_arrow(self, parent, row=0, col=0):
		"""Create a vertical arrow between rows"""
		arrow_frame = tk.Frame(parent, bg='#e8e8e8')
		arrow_frame.grid(row=row, column=col, padx=0, pady=2, sticky="ew")

		canvas = tk.Canvas(arrow_frame, bg='#e8e8e8', height=25, highlightthickness=0)
		canvas.pack(fill="both", expand=True)

		def draw(event=None):
			canvas.delete("all")
			w = canvas.winfo_width()
			h = canvas.winfo_height()
			if h > 5 and w > 10:
				center_x = w // 2
				canvas.create_line(center_x, 0, center_x, h, fill='#5a5a5a', width=3, arrow=tk.LAST, arrowshape=(10, 12, 5))

		canvas.bind('<Configure>', draw)
		arrow_frame.after(100, draw)

	def create_flow_box(self, parent, number, title, tool, color, points, optional=False):
		"""Create a visual flow box for a step"""
		# Container for the step
		box_container = tk.Frame(parent, bg='#f0f0f0')
		box_container.pack(fill="x", pady=8)

		# Main card
		card = tk.Frame(box_container, bg='white', relief=tk.SOLID, borderwidth=2, highlightbackground=color, highlightthickness=2)
		card.pack(fill="x", padx=30)

		# Colored header bar
		header_bar = tk.Frame(card, bg=color, height=6)
		header_bar.pack(fill="x")

		# Content area
		content = tk.Frame(card, bg='white', padx=20, pady=12)
		content.pack(fill="both", expand=True)

		# Top row: Step number and title
		top_row = tk.Frame(content, bg='white')
		top_row.pack(fill="x", anchor="w")

		# Step badge
		badge_text = f"STEP {number}" if not optional else f"STEP {number} (Optional)"
		step_badge = tk.Label(
			top_row,
			text=badge_text,
			font=("Segoe UI", 8, "bold"),
			bg=color,
			fg='white',
			padx=8,
			pady=3
		)
		step_badge.pack(side=tk.LEFT, padx=(0, 12))

		# Title
		title_label = tk.Label(
			top_row,
			text=title,
			font=("Segoe UI", 12, "bold"),
			bg='white',
			fg='#2c3e50'
		)
		title_label.pack(side=tk.LEFT)

		# Tool name
		tool_frame = tk.Frame(content, bg='white')
		tool_frame.pack(fill="x", anchor="w", pady=(8, 10))

		tool_label = tk.Label(
			tool_frame,
			text=f"🔧 {tool}",
			font=("Segoe UI", 9, "italic"),
			bg='white',
			fg=color
		)
		tool_label.pack(anchor="w")

		# Key points in columns
		points_frame = tk.Frame(content, bg='white')
		points_frame.pack(fill="x", anchor="w")

		for i, point in enumerate(points):
			point_label = tk.Label(
				points_frame,
				text=f"• {point}",
				font=("Segoe UI", 8),
				bg='white',
				fg='#7f8c8d',
				anchor="w"
			)
			point_label.pack(anchor="w", padx=10, pady=1)

	def create_arrow(self, parent):
		"""Create a visual arrow between steps"""
		arrow_frame = tk.Frame(parent, bg='#f0f0f0', height=35)
		arrow_frame.pack(fill="x")

		arrow_canvas = tk.Canvas(arrow_frame, bg='#f0f0f0', height=35, highlightthickness=0)
		arrow_canvas.pack(fill="x")

		# Draw arrow
		def draw_arrow(event=None):
			arrow_canvas.delete("all")
			width = arrow_canvas.winfo_width()
			if width > 1:
				center_x = width // 2
				# Vertical line
				arrow_canvas.create_line(center_x, 0, center_x, 25, fill='#95a5a6', width=3, arrow=tk.LAST, arrowshape=(10, 12, 5))

		arrow_canvas.bind('<Configure>', draw_arrow)
		arrow_frame.update_idletasks()
		draw_arrow()

	def create_flow_step_card(self, parent, step):
		"""Create a card for each flow step"""
		card = tk.Frame(parent, bg='white', relief=tk.SOLID, borderwidth=1)
		card.pack(fill="x", pady=10, padx=10)

		# Header with step number and color
		header = tk.Frame(card, bg=step['color'], height=8)
		header.pack(fill="x")

		# Content
		content = tk.Frame(card, bg='white', padx=20, pady=15)
		content.pack(fill="both", expand=True)

		# Step number and title
		title_frame = tk.Frame(content, bg='white')
		title_frame.pack(fill="x", anchor="w")

		number_label = tk.Label(
			title_frame,
			text=f"Step {step['number']}",
			font=("Segoe UI", 10, "bold"),
			bg=step['color'],
			fg='white',
			padx=10,
			pady=3
		)
		number_label.pack(side=tk.LEFT, padx=(0, 10))

		title_label = tk.Label(
			title_frame,
			text=step['title'],
			font=("Segoe UI", 13, "bold"),
			bg='white',
			fg='#2c3e50'
		)
		title_label.pack(side=tk.LEFT)

		# Tool name
		tool_label = tk.Label(
			content,
			text=f"🔧 {step['tool']}",
			font=("Segoe UI", 9, "italic"),
			bg='white',
			fg=step['color']
		)
		tool_label.pack(anchor="w", pady=(5, 10))

		# Description
		desc_label = tk.Label(
			content,
			text=step['description'],
			font=("Segoe UI", 9),
			bg='white',
			fg='#34495e',
			wraplength=800,
			justify="left"
		)
		desc_label.pack(anchor="w", pady=(0, 10))

		# Actions
		for action in step['actions']:
			action_label = tk.Label(
				content,
				text=action,
				font=("Segoe UI", 9),
				bg='white',
				fg='#7f8c8d',
				anchor="w"
			)
			action_label.pack(anchor="w", padx=20, pady=2)
		#y = (window.winfo_screenheight() // 2) - (height // 2)
		#window.geometry(f'{width}x{height}+{x}+{y}')

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
	print("Launching SysDebug & THR Tools Hub...\n")

	root = tk.Tk(baseName='MainWindow')
	app = Tools(root, default_product=selected_product)
	#app.pack(fill='both', expand=True)
	root.mainloop()
