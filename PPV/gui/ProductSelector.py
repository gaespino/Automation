"""
PPV Tools - Product Selection Welcome Window

This module provides a welcome screen for selecting the default product
to use across all PPV Tools.
"""

import tkinter as tk
from tkinter import ttk


class ProductSelectorWindow:
    """Welcome window for product selection"""

    def __init__(self, parent=None):
        """Initialize the product selector window"""
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.selected_product = None
        self.window.title("PPV Tools - Welcome")

        # Window configuration
        window_width = 600
        window_height = 600
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(False, False)

        # Make window modal
        self.window.transient(parent if parent else None)
        self.window.grab_set()

        # Configure styles
        self.setup_styles()

        # Create UI
        self.create_ui()

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#3498db',
            'success': '#10b981',
            'light': '#ecf0f1',
            'card_bg': 'white',
            'hover': '#e8f4f8'
        }

    def create_ui(self):
        """Create the UI elements"""
        # Main container
        main_container = tk.Frame(self.window, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True)

        # Header Section
        header_frame = tk.Frame(main_container, bg=self.colors['primary'], pady=30)
        header_frame.pack(fill='x')

        # Title
        title_label = tk.Label(
            header_frame,
            text="Welcome to PPV Tools",
            font=("Segoe UI", 22, "bold"),
            bg=self.colors['primary'],
            fg='white'
        )
        title_label.pack()

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Comprehensive Suite for PPV Data Analysis & Management",
            font=("Segoe UI", 10),
            bg=self.colors['primary'],
            fg=self.colors['light']
        )
        subtitle_label.pack(pady=(5, 0))

        # Info Section
        info_frame = tk.Frame(main_container, bg='#f0f0f0', pady=15)
        info_frame.pack(fill='x', padx=40)

        info_text = (
            "PPV Tools provides a comprehensive suite of utilities for analyzing "
            "and managing PPV experiment data, including:\n\n"
            "• Experiment Configuration Builder\n"
            "• MCA Report Generation & Decoding\n"
            "• PTC Loop Parser & Analysis\n"
            "• Framework Report Builder\n"
            "• Automation Flow Designer\n"
            "• File Management & Merging Tools"
        )

        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Segoe UI", 9),
            bg='#f0f0f0',
            fg=self.colors['secondary'],
            justify='left',
            wraplength=500
        )
        info_label.pack()

        # Product Selection Section
        selection_frame = tk.Frame(main_container, bg='#f0f0f0', pady=10)
        selection_frame.pack(fill='x', padx=40)

        selection_title = tk.Label(
            selection_frame,
            text="Select Default Product",
            font=("Segoe UI", 12, "bold"),
            bg='#f0f0f0',
            fg=self.colors['primary']
        )
        selection_title.pack(anchor='w', pady=(0, 10))

        selection_subtitle = tk.Label(
            selection_frame,
            text="Choose the product you'll be working with. This can be changed later in each tool.",
            font=("Segoe UI", 9),
            bg='#f0f0f0',
            fg='#7f8c8d',
            wraplength=500,
            justify='left'
        )
        selection_subtitle.pack(anchor='w', pady=(0, 15))

        # Product buttons container
        buttons_frame = tk.Frame(selection_frame, bg='#f0f0f0')
        buttons_frame.pack(pady=10)

        # Product data
        products = [
            {
                'name': 'GNR',
                'full_name': 'Granite Rapids',
                'color': '#3498db'
            },
            {
                'name': 'CWF',
                'full_name': 'Clearwater Forest',
                'color': '#9b59b6'
            },
            {
                'name': 'DMR',
                'full_name': 'Diamond Rapids',
                'color': '#e74c3c'
            }
        ]

        self.product_buttons = {}
        for i, product in enumerate(products):
            btn_frame = self.create_product_button(
                buttons_frame,
                product['name'],
                product['full_name'],
                product['color']
            )
            btn_frame.pack(side='left', padx=5)
            self.product_buttons[product['name']] = btn_frame

        # Action buttons
        action_frame = tk.Frame(main_container, bg='#f0f0f0', pady=15)
        action_frame.pack(fill='x', padx=40)

        button_container = tk.Frame(action_frame, bg='#f0f0f0')
        button_container.pack()

        # Continue button
        self.continue_btn = tk.Button(
            button_container,
            text="Continue →",
            command=self.on_continue,
            bg='#6c757d',
            fg='white',
            font=("Segoe UI", 12, "bold"),
            padx=50,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2",
            state='disabled'
        )
        self.continue_btn.pack(side='left', padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=self.on_cancel,
            bg='#95a5a6',
            fg='white',
            font=("Segoe UI", 11),
            padx=40,
            pady=15,
            relief=tk.FLAT,
            cursor="hand2"
        )
        cancel_btn.pack(side='left', padx=5)

        # Hover effects for action buttons
        self.continue_btn.bind('<Enter>', lambda e: self.continue_btn.config(
            bg=self.colors['success'] if self.continue_btn['state'] == 'normal' else '#059669'
        ) if self.continue_btn['state'] == 'normal' else None)
        self.continue_btn.bind('<Leave>', lambda e: self.continue_btn.config(
            bg=self.colors['success']
        ) if self.continue_btn['state'] == 'normal' else None)

        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg='#7f8c8d'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg='#95a5a6'))

    def create_product_button(self, parent, code, full_name, color):
        """Create a product selection button card"""
        # Main card frame - white with colored border
        card = tk.Frame(parent, bg='white', relief=tk.SOLID, borderwidth=3, highlightbackground=color, highlightthickness=3, width=160, height=130)
        card.pack_propagate(False)

        # Content
        content = tk.Frame(card, bg='white')
        content.pack(fill='both', expand=True, padx=15, pady=15)

        # Product code (large)
        code_label = tk.Label(
            content,
            text=code,
            font=("Segoe UI", 24, "bold"),
            bg='white',
            fg=color
        )
        code_label.pack(pady=(10, 8))

        # Full name
        name_label = tk.Label(
            content,
            text=full_name,
            font=("Segoe UI", 10),
            bg='white',
            fg='#495057'
        )
        name_label.pack()

        # Make entire card clickable
        def on_card_click(e=None):
            self.select_product(code, card, color)

        for widget in [card, content, code_label, name_label]:
            widget.bind('<Button-1>', on_card_click)
            widget.config(cursor='hand2')

        # Hover effect - slight background change
        def on_enter(e):
            if self.selected_product != code:
                card.config(bg='#f8f9fa')
                content.config(bg='#f8f9fa')
                code_label.config(bg='#f8f9fa')
                name_label.config(bg='#f8f9fa')

        def on_leave(e):
            if self.selected_product != code:
                card.config(bg='white')
                content.config(bg='white')
                code_label.config(bg='white')
                name_label.config(bg='white')

        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)

        # Store references
        card.color = color
        card.content = content
        card.code_label = code_label
        card.name_label = name_label

        return card

    def select_product(self, product_code, card, color):
        """Handle product selection"""
        # Reset all cards to default unfilled state
        for code, btn_card in self.product_buttons.items():
            btn_card.config(bg='white', borderwidth=3, highlightbackground=btn_card.color, highlightthickness=3)
            btn_card.content.config(bg='white')
            btn_card.code_label.config(bg='white', fg=btn_card.color)
            btn_card.name_label.config(bg='white', fg='#495057')

        # Fill selected card with its color
        card.config(bg=color, borderwidth=4, highlightbackground=color, highlightthickness=4)
        card.content.config(bg=color)
        card.code_label.config(bg=color, fg='white')
        card.name_label.config(bg=color, fg='white')

        # Update selection
        self.selected_product = product_code

        # Enable continue button
        self.continue_btn.config(state='normal', bg=self.colors['success'])

    def on_continue(self):
        """Handle continue button click"""
        if self.selected_product:
            self.window.destroy()

    def on_cancel(self):
        """Handle cancel/close"""
        self.selected_product = None
        self.window.destroy()

    def show(self):
        """Show the window and wait for user selection"""
        self.window.wait_window()
        return self.selected_product


def show_product_selector(parent=None):
    """Show the product selector and return the selected product"""
    selector = ProductSelectorWindow(parent)
    return selector.show()


if __name__ == "__main__":
    # Test the product selector
    selected = show_product_selector()
    print(f"Selected product: {selected}")
