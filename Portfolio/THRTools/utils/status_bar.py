"""
Reusable status bar component for PPV GUI applications.

Provides a colored status message bar that can display info, success, warning, and error messages.
Messages auto-clear after a timeout for info/success types.
"""

import tkinter as tk
from typing import Optional


class StatusBar:
    """
    Reusable status message bar widget.

    Features:
    - Color-coded messages (info/success/warning/error)
    - Auto-clear for info and success messages
    - Single-line or two-line display
    - Consistent styling across applications
    """

    def __init__(self, parent: tk.Widget, height: int = 50):
        """
        Initialize the status bar.

        Args:
            parent: Parent widget to attach the status bar to
            height: Height of the status bar in pixels (default: 50)
        """
        self.parent = parent
        self._clear_timer: Optional[str] = None

        # Create status bar frame
        self.frame = tk.Frame(parent, bg='#ecf0f1', relief=tk.RIDGE, bd=2, height=height)
        self.frame.grid_propagate(False)
        self.frame.columnconfigure(0, weight=1)

        # Create status label
        self.label = tk.Label(
            self.frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg='#ecf0f1',
            fg='#2c3e50',
            anchor='w',
            padx=15,
            pady=10,
            wraplength=1200,  # Allow text wrapping for long messages
            justify=tk.LEFT
        )
        self.label.pack(fill=tk.BOTH, expand=True)

    def show(self, message: str, msg_type: str = 'info', auto_clear: bool = True):
        """
        Show a status message with appropriate color coding.

        Args:
            message: Message text to display
            msg_type: Type of message - 'info', 'success', 'warning', 'error'
            auto_clear: If True, auto-clear info/success messages after 5 seconds
        """
        colors = {
            'info': ('#3498db', '#ecf0f1', '#2c3e50'),      # Blue border, light bg, dark text
            'success': ('#27ae60', '#d5f4e6', '#145a32'),   # Green border, light green bg, dark green text
            'warning': ('#f39c12', '#fef5e7', '#7d6608'),   # Orange border, light yellow bg, dark orange text
            'error': ('#e74c3c', '#fadbd8', '#78281f')      # Red border, light red bg, dark red text
        }

        border_color, bg_color, text_color = colors.get(msg_type, colors['info'])

        # Update frame and label styling
        self.frame.config(bg=border_color, bd=2)
        self.label.config(
            text=message,
            bg=bg_color,
            fg=text_color,
            font=("Segoe UI", 9, "bold" if msg_type in ['error', 'warning'] else 'normal')
        )

        # Cancel any existing timer
        if self._clear_timer:
            try:
                self.parent.after_cancel(self._clear_timer)
            except:
                pass
            self._clear_timer = None

        # Auto-clear success and info messages after 5 seconds
        if auto_clear and msg_type in ['info', 'success']:
            self._clear_timer = self.parent.after(5000, lambda: self.show("Ready", 'info', False))

    def grid(self, **kwargs):
        """
        Grid the status bar frame.

        Args:
            **kwargs: Grid options (row, column, sticky, padx, pady, etc.)
        """
        self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        """
        Pack the status bar frame.

        Args:
            **kwargs: Pack options (side, fill, expand, padx, pady, etc.)
        """
        self.frame.pack(**kwargs)

    def clear(self):
        """Clear the status message and reset to default state."""
        self.show("Ready", 'info', False)
