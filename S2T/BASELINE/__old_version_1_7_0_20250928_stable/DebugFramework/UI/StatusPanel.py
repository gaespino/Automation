import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from datetime import datetime
import queue
import time
from typing import Dict, Any, Optional, Callable

print(' -- Debug Framework Execution Status Panel -- rev 1.7')

class StatusExecutionPanel:
    """
    Shared status execution panel that can be used by both Control Panel and Automation interfaces.
    Provides real-time execution monitoring, progress tracking, and logging capabilities.
    """
    
    def __init__(self, parent_frame: ttk.Frame, 
                 dual_progress: bool = True,
                 show_experiment_stats: bool = True,
                 logger_callback: Optional[Callable] = None):
        """
        Initialize the status execution panel.
        
        Args:
            parent_frame: Parent frame to contain this panel
            dual_progress: Whether to show dual progress bars (overall + iteration)
            show_experiment_stats: Whether to show current experiment statistics
            logger_callback: Optional callback for external logging
        """
        self.parent_frame = parent_frame
        self.dual_progress = dual_progress
        self.show_experiment_stats = show_experiment_stats
        self.logger_callback = logger_callback
        
        # Progress tracking variables
        self.total_experiments = 0
        self.current_experiment_index = 0
        self.current_iteration = 0
        self.total_iterations_in_experiment = 0
        self.current_iteration_progress = 0.0
        self.strategy_progress = 0.0
        
        # Statistics tracking
        self.start_time = None
        self.last_iteration_time = None
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
        # UI State tracking
        self._last_status_priority = 0
        self._strategy_progress_active = False
        
        # Create the panel
        self.setup_styles()
        self.create_panel()
        
        # Initialize with default messages
        self.log_status("Status panel initialized")
        self.log_status("Ready for execution...")

    def setup_styles(self):
        """Configure ttk styles for consistent appearance."""
        self.style = ttk.Style()
        
        # Try to use alt theme for consistency
        try:
            self.style.theme_use('alt')
        except:
            self.style.theme_use('clam')
        
        # Progress bar styles
        self.style.configure("Overall.Horizontal.TProgressbar",
                           troughcolor='#404040',
                           background='#2196F3',
                           lightcolor='#2196F3',
                           darkcolor='#1976D2',
                           borderwidth=1,
                           relief='flat')
        
        self.style.configure("Iteration.Horizontal.TProgressbar",
                           troughcolor='#404040',
                           background='#4CAF50',
                           lightcolor='#4CAF50',
                           darkcolor='#388E3C',
                           borderwidth=1,
                           relief='flat')
        
        # State-specific styles
        state_styles = {
            'Running': ('#2196F3', '#1976D2'),
            'Warning': ('#FF9800', '#F57C00'),
            'Error': ('#F44336', '#D32F2F'),
            'Boot': ('#FF9800', '#F57C00')
        }
        
        for state, (bg, dark) in state_styles.items():
            self.style.configure(f"Overall.{state}.Horizontal.TProgressbar",
                               background=bg, lightcolor=bg, darkcolor=dark)
            self.style.configure(f"Iteration.{state}.Horizontal.TProgressbar",
                               background=bg, lightcolor=bg, darkcolor=dark)

    def create_panel(self):
        """Create the complete status panel UI."""
        # Main container
        self.main_container = ttk.Frame(self.parent_frame)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(self.main_container, text="Execution Status", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create sections
        self.create_progress_section()
        self.create_statistics_section()
        if self.show_experiment_stats:
            self.create_experiment_stats_section()
        self.create_log_section()

    def create_progress_section(self):
        """Create the progress tracking section."""
        progress_frame = ttk.LabelFrame(self.main_container, text="Execution Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Strategy and test info
        self.strategy_label = ttk.Label(progress_frame, text="Strategy: Ready")
        self.strategy_label.pack(anchor="w")
        
        self.test_name_label = ttk.Label(progress_frame, text="Test: None", foreground="blue")
        self.test_name_label.pack(anchor="w")
        
        if self.dual_progress:
            self.create_dual_progress_bars(progress_frame)
        else:
            self.create_single_progress_bar(progress_frame)
        
        # Status and phase info
        status_info = ttk.Frame(progress_frame)
        status_info.pack(fill=tk.X, pady=(5, 0))
        
        self.iteration_status_label = ttk.Label(status_info, text="Status: Idle")
        self.iteration_status_label.pack(side=tk.LEFT)
        
        self.phase_label = ttk.Label(status_info, text="", foreground="orange")
        self.phase_label.pack(side=tk.RIGHT)

    def create_dual_progress_bars(self, parent):
        """Create dual progress bar system (overall + iteration)."""
        # Overall progress bar
        overall_frame = ttk.Frame(parent)
        overall_frame.pack(fill=tk.X, pady=(10, 5))
        
        overall_info = ttk.Frame(overall_frame)
        overall_info.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(overall_info, text="Overall Progress:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.overall_percentage_label = ttk.Label(overall_info, text="0%", font=("Arial", 10, "bold"))
        self.overall_percentage_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.overall_experiment_label = ttk.Label(overall_info, text="(0/0 experiments)")
        self.overall_experiment_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.overall_eta_label = ttk.Label(overall_info, text="")
        self.overall_eta_label.pack(side=tk.RIGHT)
        
        self.overall_progress_var = tk.DoubleVar()
        self.overall_progress_bar = ttk.Progressbar(overall_frame, variable=self.overall_progress_var,
                                                   maximum=100, style="Overall.Horizontal.TProgressbar")
        self.overall_progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Current iteration progress bar
        iteration_frame = ttk.Frame(parent)
        iteration_frame.pack(fill=tk.X, pady=(5, 5))
        
        iteration_info = ttk.Frame(iteration_frame)
        iteration_info.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(iteration_info, text="Current Iteration:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.iteration_percentage_label = ttk.Label(iteration_info, text="0%", font=("Arial", 10, "bold"))
        self.iteration_percentage_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.iteration_progress_label = ttk.Label(iteration_info, text="(0/0)")
        self.iteration_progress_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.iteration_speed_label = ttk.Label(iteration_info, text="")
        self.iteration_speed_label.pack(side=tk.RIGHT)
        
        self.iteration_progress_var = tk.DoubleVar()
        self.iteration_progress_bar = ttk.Progressbar(iteration_frame, variable=self.iteration_progress_var,
                                                     maximum=100, style="Iteration.Horizontal.TProgressbar")
        self.iteration_progress_bar.pack(fill=tk.X, pady=(0, 5))

    def create_single_progress_bar(self, parent):
        """Create single progress bar system."""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(10, 5))
        
        progress_info = ttk.Frame(progress_frame)
        progress_info.pack(fill=tk.X, pady=(0, 2))
        
        ttk.Label(progress_info, text="Progress:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.progress_percentage_label = ttk.Label(progress_info, text="0%", font=("Arial", 10, "bold"))
        self.progress_percentage_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.progress_detail_label = ttk.Label(progress_info, text="(0/0)")
        self.progress_detail_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.progress_eta_label = ttk.Label(progress_info, text="")
        self.progress_eta_label.pack(side=tk.RIGHT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, style="Overall.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

    def create_statistics_section(self):
        """Create the statistics section."""
        stats_frame = ttk.LabelFrame(self.main_container, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Counters
        counters = ttk.Frame(stats_frame)
        counters.pack(fill=tk.X)
        
        self.pass_count_label = ttk.Label(counters, text="✓ Pass: 0", foreground="green")
        self.pass_count_label.pack(side=tk.LEFT)
        
        self.fail_count_label = ttk.Label(counters, text="✗ Fail: 0", foreground="red")
        self.fail_count_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.skip_count_label = ttk.Label(counters, text="⊘ Skip: 0", foreground="orange")
        self.skip_count_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.elapsed_time_label = ttk.Label(counters, text="Time: 00:00")
        self.elapsed_time_label.pack(side=tk.RIGHT)

    def create_experiment_stats_section(self):
        """Create current experiment statistics section."""
        exp_stats_frame = ttk.LabelFrame(self.main_container, text="Current Experiment", padding=10)
        exp_stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.exp_iteration_label = ttk.Label(exp_stats_frame, text="Iteration: 0/0")
        self.exp_iteration_label.pack(anchor="w")
        
        self.exp_pass_rate_label = ttk.Label(exp_stats_frame, text="Pass Rate: 0%")
        self.exp_pass_rate_label.pack(anchor="w")
        
        self.exp_recommendation_label = ttk.Label(exp_stats_frame, text="Recommendation: --")
        self.exp_recommendation_label.pack(anchor="w")

    def create_log_section(self):
        """Create the logging section."""
        log_frame = ttk.LabelFrame(self.main_container, text="Status Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log container
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbar
        self.status_log = tk.Text(log_container, bg="black", fg="white", 
                                 font=("Consolas", 10), wrap=tk.WORD, 
                                 state=tk.DISABLED, width=45, height=15,
                                 insertbackground="white",
                                 selectbackground="darkblue",
                                 selectforeground="white")
        
        log_scrollbar = ttk.Scrollbar(log_container, orient="vertical", 
                                     command=self.status_log.yview)
        self.status_log.configure(yscrollcommand=log_scrollbar.set)
        
        self.status_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear", command=self.clear_status_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save", command=self.save_status_log).pack(side=tk.LEFT, padx=(5, 0))
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_controls, text="Auto-scroll", 
                       variable=self.auto_scroll_var).pack(side=tk.RIGHT)

    # === PROGRESS UPDATE METHODS ===
    
    def update_overall_progress(self, current_index: int, total_count: int, 
                               current_progress: float = 0.0):
        """Update overall progress across all experiments/nodes."""
        self.current_experiment_index = current_index
        self.total_experiments = total_count
        
        if total_count == 0:
            progress = 0
        else:
            progress = ((current_index + current_progress) / total_count) * 100
        
        if self.dual_progress and hasattr(self, 'overall_progress_var'):
            self.overall_progress_var.set(max(0, min(100, progress)))
            self.overall_percentage_label.configure(text=f"{int(progress)}%")
            self.overall_experiment_label.configure(text=f"({current_index + 1}/{total_count} experiments)")
        elif hasattr(self, 'progress_var'):
            self.progress_var.set(max(0, min(100, progress)))
            self.progress_percentage_label.configure(text=f"{int(progress)}%")
            self.progress_detail_label.configure(text=f"({current_index + 1}/{total_count})")

    def update_iteration_progress(self, current_iter: int, total_iters: int, 
                                 progress_percent: float = None):
        """Update current iteration progress."""
        self.current_iteration = current_iter
        self.total_iterations_in_experiment = total_iters
        
        if progress_percent is None:
            progress_percent = (current_iter / total_iters * 100) if total_iters > 0 else 0
        
        self.current_iteration_progress = progress_percent / 100.0
        
        if self.dual_progress and hasattr(self, 'iteration_progress_var'):
            self.iteration_progress_var.set(max(0, min(100, progress_percent)))
            self.iteration_percentage_label.configure(text=f"{int(progress_percent)}%")
            self.iteration_progress_label.configure(text=f"({current_iter}/{total_iters})")

    def update_strategy_info(self, experiment_name: str = "", strategy_type: str = "", 
                           test_name: str = "", status: str = "Idle"):
        """Update strategy and test information."""
        if experiment_name and hasattr(self, 'strategy_label'):
            self.strategy_label.configure(text=f"Experiment: {experiment_name}")
        
        if strategy_type or test_name:
            if hasattr(self, 'test_name_label'):
                display_text = f"Strategy: {strategy_type}"
                if test_name:
                    display_text += f" - {test_name}"
                self.test_name_label.configure(text=display_text)
        
        if status and hasattr(self, 'iteration_status_label'):
            self.iteration_status_label.configure(text=f"Status: {status}")

    def update_statistics(self, pass_count: int = None, fail_count: int = None, 
                         skip_count: int = None, result_status: str = None):
        """Update execution statistics."""
        # Update counters based on result status
        if result_status:
            if result_status.upper() in ["PASS", "SUCCESS", "*"]:
                self.pass_count += 1
            elif result_status.upper() in ["FAIL", "FAILED", "ERROR"]:
                self.fail_count += 1
            else:
                self.skip_count += 1
        
        # Update with provided values
        if pass_count is not None:
            self.pass_count = pass_count
        if fail_count is not None:
            self.fail_count = fail_count
        if skip_count is not None:
            self.skip_count = skip_count
        
        # Update labels
        self.pass_count_label.configure(text=f"✓ Pass: {self.pass_count}")
        self.fail_count_label.configure(text=f"✗ Fail: {self.fail_count}")
        self.skip_count_label.configure(text=f"⊘ Skip: {self.skip_count}")

    def update_experiment_stats(self, iteration: int = None, total_iterations: int = None,
                               pass_rate: float = None, recommendation: str = None):
        """Update current experiment statistics (if enabled)."""
        if not self.show_experiment_stats:
            return
        
        if iteration is not None and total_iterations is not None:
            self.exp_iteration_label.configure(text=f"Iteration: {iteration}/{total_iterations}")
        
        if pass_rate is not None:
            self.exp_pass_rate_label.configure(text=f"Pass Rate: {pass_rate:.1f}%")
        
        if recommendation is not None:
            self.exp_recommendation_label.configure(text=f"Recommendation: {recommendation}")

    def update_timing_display(self):
        """Update timing information."""
        if self.start_time is None:
            self.start_time = time.time()
        
        current_time = time.time()
        elapsed_seconds = current_time - self.start_time
        elapsed_str = self._format_time(elapsed_seconds)
        
        self.elapsed_time_label.configure(text=f"Time: {elapsed_str}")
        
        # Update ETA if we have progress data
        self._update_eta_display(elapsed_seconds)

    def _update_eta_display(self, elapsed_seconds: float):
        """Update ETA display based on current progress."""
        try:
            if self.dual_progress and hasattr(self, 'overall_progress_var'):
                current_progress = self.overall_progress_var.get()
            elif hasattr(self, 'progress_var'):
                current_progress = self.progress_var.get()
            else:
                return
            
            if current_progress > 0 and elapsed_seconds > 0:
                total_estimated_time = (elapsed_seconds / current_progress) * 100
                remaining_time = total_estimated_time - elapsed_seconds
                
                if remaining_time > 0:
                    eta_str = self._format_time(remaining_time)
                    if self.dual_progress and hasattr(self, 'overall_eta_label'):
                        self.overall_eta_label.configure(text=f"ETA: {eta_str}")
                    elif hasattr(self, 'progress_eta_label'):
                        self.progress_eta_label.configure(text=f"ETA: {eta_str}")
        except Exception:
            pass  # Ignore ETA calculation errors

    def _format_time(self, seconds: float) -> str:
        """Format seconds into HH:MM:SS or MM:SS format."""
        if seconds < 0:
            return "00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    # === LOGGING METHODS ===
    
    def log_status(self, message: str, level: str = "info"):
        """Add message to status log with timestamp and level."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        color_map = {
            "error": "red",
            "warning": "yellow", 
            "success": "green",
            "info": "white"
        }
        color = color_map.get(level.lower(), "white")
        prefix = level.upper()
        
        log_entry = f"[{timestamp}] {prefix}: {message}\n"
        
        self.status_log.configure(state=tk.NORMAL)
        
        # Insert with color
        start_pos = self.status_log.index(tk.END)
        self.status_log.insert(tk.END, log_entry)
        end_pos = self.status_log.index(tk.END)
        
        # Apply color tag
        tag_name = f"level_{level}_{timestamp.replace(':', '_')}"
        self.status_log.tag_add(tag_name, start_pos, end_pos)
        self.status_log.tag_config(tag_name, foreground=color)
        
        if self.auto_scroll_var.get():
            self.status_log.see(tk.END)
        
        self.status_log.configure(state=tk.DISABLED)
        
        # External logging callback
        if self.logger_callback:
            self.logger_callback(message, level)
        
        # Keep only last 500 lines
        self._trim_log()

    def _trim_log(self):
        """Keep only the last 500 lines in the log."""
        lines = self.status_log.get("1.0", tk.END).split('\n')
        if len(lines) > 500:
            self.status_log.configure(state=tk.NORMAL)
            self.status_log.delete("1.0", f"{len(lines)-500}.0")
            self.status_log.configure(state=tk.DISABLED)

    def clear_status_log(self):
        """Clear the status log."""
        self.status_log.configure(state=tk.NORMAL)
        self.status_log.delete("1.0", tk.END)
        self.status_log.configure(state=tk.DISABLED)
        self.log_status("Status log cleared")

    def save_status_log(self):
        """Save status log to file."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Status Log"
            )
            if file_path:
                log_content = self.status_log.get("1.0", tk.END)
                with open(file_path, 'w') as f:
                    f.write(log_content)
                self.log_status(f"Status log saved to: {file_path}", "success")
        except Exception as e:
            self.log_status(f"Error saving log: {str(e)}", "error")

    # === RESET AND CLEANUP METHODS ===
    
    def reset_progress_tracking(self):
        """Reset all progress tracking variables."""
        self.start_time = None
        self.last_iteration_time = None
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
        # Reset progress bars
        if self.dual_progress:
            if hasattr(self, 'overall_progress_var'):
                self.overall_progress_var.set(0)
            if hasattr(self, 'iteration_progress_var'):
                self.iteration_progress_var.set(0)
            
            # Reset labels
            if hasattr(self, 'overall_percentage_label'):
                self.overall_percentage_label.configure(text="0%")
            if hasattr(self, 'iteration_percentage_label'):
                self.iteration_percentage_label.configure(text="0%")
            if hasattr(self, 'overall_experiment_label'):
                self.overall_experiment_label.configure(text="(0/0 experiments)")
            if hasattr(self, 'iteration_progress_label'):
                self.iteration_progress_label.configure(text="(0/0)")
        else:
            if hasattr(self, 'progress_var'):
                self.progress_var.set(0)
            if hasattr(self, 'progress_percentage_label'):
                self.progress_percentage_label.configure(text="0%")
            if hasattr(self, 'progress_detail_label'):
                self.progress_detail_label.configure(text="(0/0)")
        
        # Reset statistics display
        self.pass_count_label.configure(text="✓ Pass: 0")
        self.fail_count_label.configure(text="✗ Fail: 0")
        self.skip_count_label.configure(text="⊘ Skip: 0")
        self.elapsed_time_label.configure(text="Time: 00:00")
        
        # Reset ETA labels
        if hasattr(self, 'overall_eta_label'):
            self.overall_eta_label.configure(text="")
        if hasattr(self, 'progress_eta_label'):
            self.progress_eta_label.configure(text="")
        
        # Reset experiment stats if enabled
        if self.show_experiment_stats:
            self.exp_iteration_label.configure(text="Iteration: 0/0")
            self.exp_pass_rate_label.configure(text="Pass Rate: 0%")
            self.exp_recommendation_label.configure(text="Recommendation: --")
        
        # Reset phase label
        if hasattr(self, 'phase_label'):
            self.phase_label.configure(text="")

    def set_progress_bar_style(self, bar_type: str, style_name: str):
        """Set progress bar style."""
        try:
            if bar_type == 'overall' and hasattr(self, 'overall_progress_bar'):
                self.overall_progress_bar.configure(style=style_name)
            elif bar_type == 'iteration' and hasattr(self, 'iteration_progress_bar'):
                self.iteration_progress_bar.configure(style=style_name)
            elif bar_type == 'single' and hasattr(self, 'progress_bar'):
                self.progress_bar.configure(style=style_name)
        except Exception as e:
            self.log_status(f"Error setting progress bar style: {e}", "error")

    def get_panel_frame(self) -> ttk.Frame:
        """Get the main panel frame for embedding in other interfaces."""
        return self.main_container

    def reset_counters(self):
        """Reset all counters in status panel"""
        try:
            self.pass_count = 0
            self.fail_count = 0
            self.skip_count = 0
            self.start_time = None
            self.last_iteration_time = None
            
            # Update labels
            if hasattr(self, 'pass_count_label'):
                self.pass_count_label.configure(text="✓ Pass: 0")
            if hasattr(self, 'fail_count_label'):
                self.fail_count_label.configure(text="✗ Fail: 0")
            if hasattr(self, 'skip_count_label'):
                self.skip_count_label.configure(text="⊘ Skip: 0")
            if hasattr(self, 'elapsed_time_label'):
                self.elapsed_time_label.configure(text="Time: 00:00")
                
        except Exception as e:
            print(f"Status panel counter reset error: {e}")