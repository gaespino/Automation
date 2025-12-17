"""
MCA Single Line Decoder UI
Interactive interface for decoding individual MCA register values
Supports CHA, LLC, CORE, and MEM decoders for multiple products
"""

import sys
import os

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re

try:
    from ..Decoder import decoder as mcparse
    from ..Decoder.decoder import extract_bits
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from Decoder import decoder as mcparse
    from Decoder.decoder import extract_bits


class MCADecoderGUI:
    """
    Single MCA register decoder with dynamic fields based on product and decoder type
    """

    def __init__(self, root):
        self.root = root
        self.root.title("MCA Single Line Decoder")
        self.root.geometry("900x700")

        # Product configurations
        self.products = ['GNR', 'CWF', 'DMR']
        self.decoder_types = {
            'CHA/CCF': {
                'description': 'CHA (Caching Agent) / CCF Decoder',
                'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC', 'MC_MISC3'],
                'decode_method': 'cha'
            },
            'LLC': {
                'description': 'Last Level Cache Decoder',
                'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
                'decode_method': 'llc'
            },
            'CORE': {
                'description': 'CPU Core Decoder (ML2, DCU, IFU, DTLB, etc.)',
                'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
                'decode_method': 'core',
                'subtypes': ['ML2', 'DCU', 'IFU', 'DTLB', 'L2', 'BBL', 'BUS', 'MEC', 'AGU', 'IC']
            },
            'MEMORY': {
                'description': 'Memory Subsystem Decoder (B2CMI, MSE, MCCHAN)',
                'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
                'decode_method': 'mem',
                'subtypes': ['B2CMI', 'MSE', 'MCCHAN']
            },
            'IO': {
                'description': 'IO Subsystem Decoder (UBOX, UPI, ULA)',
                'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
                'decode_method': 'io',
                'subtypes': ['UBOX', 'UPI', 'ULA']
            },
            'FIRST ERROR': {
                'description': 'First Error Logger - UBOX MCERR/IERR Logging',
                'registers': ['MCERRLOGGINGREG', 'IERRLOGGINGREG'],
                'decode_method': 'first_error'
            }
        }

        # Initialize decoder
        self.current_decoder = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the complete user interface"""
        # Configure grid weights
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Header frame with color accent
        header_frame = tk.Frame(self.root, bg='#e74c3c', height=12)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)

        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=2)

        # Configuration Section
        config_frame = tk.LabelFrame(main_frame, text="Configuration",
                                    font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Product selection
        ttk.Label(config_frame, text="Product:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.product_var = tk.StringVar(value=self.products[0])
        product_combo = ttk.Combobox(config_frame, textvariable=self.product_var,
                                     values=self.products, state='readonly', width=15)
        product_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        product_combo.bind('<<ComboboxSelected>>', self.on_product_changed)

        # Decoder type selection
        ttk.Label(config_frame, text="Decoder Type:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.decoder_var = tk.StringVar(value=list(self.decoder_types.keys())[0])
        decoder_combo = ttk.Combobox(config_frame, textvariable=self.decoder_var,
                                     values=list(self.decoder_types.keys()),
                                     state='readonly', width=20)
        decoder_combo.grid(row=0, column=3, sticky=tk.W)
        decoder_combo.bind('<<ComboboxSelected>>', self.on_decoder_changed)

        # Decoder description
        self.desc_label = ttk.Label(config_frame, text="", foreground="gray")
        self.desc_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))

        # Subtype frame (hidden by default)
        self.subtype_frame = ttk.Frame(config_frame)
        self.subtype_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        ttk.Label(self.subtype_frame, text="Bank/Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.subtype_var = tk.StringVar()
        self.subtype_combo = ttk.Combobox(self.subtype_frame, textvariable=self.subtype_var,
                                         state='readonly', width=15)
        self.subtype_combo.grid(row=0, column=1, sticky=tk.W)
        self.subtype_frame.grid_remove()  # Hide initially

        # Register Input Section
        self.input_frame = tk.LabelFrame(main_frame, text="Register Values",
                                        font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        self.input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Dynamic register entry fields
        self.register_entries = {}
        self.register_labels = {}

        # Decode Button
        decode_btn = tk.Button(main_frame, text="Decode MCA", command=self.decode_mca,
                              bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
                              padx=30, pady=10, relief=tk.FLAT, cursor="hand2")
        decode_btn.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        # Results Section
        results_frame = tk.LabelFrame(main_frame, text="Decoded Results",
                                     font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80,
                                                     font=("Consolas", 10), wrap=tk.WORD,
                                                     bg="#f8f9fa", relief=tk.FLAT,
                                                     borderwidth=1, highlightthickness=1,
                                                     highlightbackground="#dee2e6")
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Action buttons frame
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        copy_btn = tk.Button(buttons_frame, text="Copy Results", command=self.copy_results,
                           bg="#3498db", fg="white", font=("Segoe UI", 9, "bold"),
                           padx=20, pady=8, relief=tk.FLAT, cursor="hand2")
        copy_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(buttons_frame, text="Clear All", command=self.clear_all,
                            bg="#95a5a6", fg="white", font=("Segoe UI", 9, "bold"),
                            padx=20, pady=8, relief=tk.FLAT, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Initialize UI state
        self.on_decoder_changed()

    def on_product_changed(self, event=None):
        """Handle product selection change"""
        product = self.product_var.get()

        # Update decoder availability based on product
        if product == 'DMR':
            # DMR uses CCF instead of CHA, no separate LLC
            if self.decoder_var.get() == 'LLC':
                self.decoder_var.set('CHA/CCF')

        # Reinitialize decoder
        try:
            self.current_decoder = mcparse.mcadata(product=product)
            self.update_results(f"Initialized decoder for {product}\n", clear=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize decoder: {str(e)}")

    def on_decoder_changed(self, event=None):
        """Handle decoder type change - update register fields"""
        decoder_type = self.decoder_var.get()
        config = self.decoder_types[decoder_type]

        # Update description
        self.desc_label.config(text=config['description'])

        # Show/hide subtype selection
        if 'subtypes' in config:
            self.subtype_combo['values'] = config['subtypes']
            self.subtype_var.set(config['subtypes'][0])
            self.subtype_frame.grid()
        else:
            self.subtype_frame.grid_remove()

        # Clear existing register fields
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        self.register_entries.clear()
        self.register_labels.clear()

        # Create new register fields
        registers = config['registers']
        for idx, reg_name in enumerate(registers):
            # Label
            label = ttk.Label(self.input_frame, text=f"{reg_name}:")
            label.grid(row=idx, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            self.register_labels[reg_name] = label

            # Entry with validation hint
            entry_frame = ttk.Frame(self.input_frame)
            entry_frame.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=5)
            self.input_frame.columnconfigure(1, weight=1)

            entry = ttk.Entry(entry_frame, width=50)
            entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
            entry_frame.columnconfigure(0, weight=1)

            hint = ttk.Label(entry_frame, text="(e.g., 0x1234ABCD)",
                           foreground="gray", font=("Segoe UI", 8))
            hint.grid(row=0, column=1, padx=(5, 0))

            self.register_entries[reg_name] = entry

            # Add example values on right-click
            entry.bind('<Button-3>', lambda e, r=reg_name: self.show_example(r))

    def show_example(self, register_name):
        """Show example values for a register"""
        examples = {
            'MC_STATUS': '0x9C00000040000000',
            'MC_ADDR': '0x0000000123456789',
            'MC_MISC': '0x0000000000000080',
            'MC_MISC3': '0x0000000000000000'
        }

        if register_name in examples:
            entry = self.register_entries[register_name]
            current = entry.get()
            if not current:
                entry.insert(0, examples[register_name])

    def validate_hex_value(self, value):
        """Validate and normalize hex value"""
        if not value:
            return None

        # Remove whitespace
        value = value.strip()

        # Add 0x prefix if missing
        if not value.startswith('0x') and not value.startswith('0X'):
            value = '0x' + value

        # Validate hex format
        try:
            int(value, 16)
            return value.upper()
        except ValueError:
            return None

    def decode_mca(self):
        """Main decode function - processes register values"""
        # Get configuration
        product = self.product_var.get()
        decoder_type = self.decoder_var.get()
        config = self.decoder_types[decoder_type]

        # Initialize decoder if needed
        if self.current_decoder is None:
            try:
                self.current_decoder = mcparse.mcadata(product=product)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize decoder: {str(e)}")
                return

        # Get and validate register values
        register_values = {}
        errors = []

        for reg_name, entry in self.register_entries.items():
            value = entry.get()
            if value:  # Only validate non-empty fields
                validated = self.validate_hex_value(value)
                if validated:
                    register_values[reg_name] = validated
                else:
                    errors.append(f"{reg_name}: Invalid hex format")

        # Check for required fields based on decoder type
        if decoder_type == 'FIRST ERROR':
            # At least one of MCERRLOGGINGREG or IERRLOGGINGREG required
            if not register_values.get('MCERRLOGGINGREG') and not register_values.get('IERRLOGGINGREG'):
                errors.append("At least one of MCERRLOGGINGREG or IERRLOGGINGREG is required")
        else:
            # MC_STATUS is required for all other decoders
            if 'MC_STATUS' not in register_values or not register_values['MC_STATUS']:
                errors.append("MC_STATUS is required")

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        # Clear previous results
        self.update_results("", clear=True)

        # Perform decoding based on decoder type
        try:
            method = config['decode_method']

            if method == 'cha':
                self.decode_cha(register_values, product)
            elif method == 'llc':
                self.decode_llc(register_values, product)
            elif method == 'core':
                self.decode_core(register_values, product)
            elif method == 'mem':
                self.decode_memory(register_values, product)
            elif method == 'io':
                self.decode_io(register_values, product)
            elif method == 'first_error':
                self.decode_first_error(register_values, product)
            elif method == 'mem':
                self.decode_memory(register_values, product)

        except Exception as e:
            self.update_results(f"ERROR: {str(e)}\n\n")
            import traceback
            self.update_results(traceback.format_exc())

    def decode_cha(self, values, product):
        """Decode CHA/CCF MCA registers"""
        self.update_results("╔" + "═" * 78 + "╗\n")
        self.update_results(f"║ CHA/CCF MCA DECODE - {product:<62} ║\n")
        self.update_results("╚" + "═" * 78 + "╝\n\n")

        mc_status = values.get('MC_STATUS', '')
        mc_addr = values.get('MC_ADDR', '')
        mc_misc = values.get('MC_MISC', '')
        mc_misc3 = values.get('MC_MISC3', '')

        # Display raw values
        self.update_results("┌─ RAW REGISTER VALUES " + "─" * 56 + "┐\n")
        self.update_results(f"│ MC_STATUS:  {mc_status:<64} │\n")
        if mc_addr:
            self.update_results(f"│ MC_ADDR:    {mc_addr:<64} │\n")
        if mc_misc:
            self.update_results(f"│ MC_MISC:    {mc_misc:<64} │\n")
        if mc_misc3:
            self.update_results(f"│ MC_MISC3:   {mc_misc3:<64} │\n")
        self.update_results("└" + "─" * 78 + "┘\n\n")

        # Create a minimal decoder instance to use decoding methods
        # We need to create a dummy dataframe to initialize decoder
        import pandas as pd
        dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
        dec = mcparse.decoder(data=dummy_df, product=product)

        # Decode MC_STATUS fields
        self.update_results("┌─ MC_STATUS DECODE " + "─" * 59 + "┐\n")

        try:
            # MSCOD (bits 16-31)
            mscod = dec.cha_decoder(value=mc_status, type='MC DECODE')
            self.update_results(f"│ MSCOD (Error Type):   {mscod:<55} │\n")

            # VAL bit (bit 63)
            val_bit = extract_bits(mc_status, 63, 63)
            val_status = 'Valid' if val_bit == 1 else 'Invalid'
            self.update_results(f"│ VAL (Valid):          {val_bit} - {val_status:<47} │\n")

            # UC bit (bit 61)
            uc_bit = extract_bits(mc_status, 61, 61)
            uc_status = 'Uncorrected' if uc_bit == 1 else 'Corrected'
            self.update_results(f"│ UC (Uncorrected):     {uc_bit} - {uc_status:<47} │\n")

            # PCC bit (bit 57)
            pcc_bit = extract_bits(mc_status, 57, 57)
            pcc_status = 'Corrupted' if pcc_bit == 1 else 'Not Corrupted'
            self.update_results(f"│ PCC (Proc Context):   {pcc_bit} - {pcc_status:<47} │\n")

            # ADDRV bit (bit 58)
            addrv_bit = extract_bits(mc_status, 58, 58)
            addrv_status = 'Valid' if addrv_bit == 1 else 'Invalid'
            self.update_results(f"│ ADDRV (Addr Valid):   {addrv_bit} - {addrv_status:<47} │\n")

            # MISCV bit (bit 59)
            miscv_bit = extract_bits(mc_status, 59, 59)
            miscv_status = 'Valid' if miscv_bit == 1 else 'Invalid'
            self.update_results(f"│ MISCV (Misc Valid):   {miscv_bit} - {miscv_status:<47} │\n")

        except Exception as e:
            self.update_results(f"│ Error: {str(e):<71} │\n")

        self.update_results("└" + "─" * 78 + "┘\n\n")

        # Decode MC_MISC if available
        if mc_misc:
            self.update_results("┌─ MC_MISC DECODE " + "─" * 61 + "┐\n")
            try:
                orig_req = dec.cha_decoder(value=mc_misc, type='Orig Req')
                opcode = dec.cha_decoder(value=mc_misc, type='Opcode')
                cache_state = dec.cha_decoder(value=mc_misc, type='cachestate')
                tor_id = dec.cha_decoder(value=mc_misc, type='TorID')
                tor_fsm = dec.cha_decoder(value=mc_misc, type='TorFSM')

                self.update_results(f"│ Original Request:  {orig_req:<57} │\n")
                self.update_results(f"│ Opcode:            {opcode:<57} │\n")
                self.update_results(f"│ Cache State:       {cache_state:<57} │\n")
                self.update_results(f"│ TOR ID:            {tor_id:<57} │\n")
                self.update_results(f"│ TOR FSM:           {tor_fsm:<57} │\n")
            except Exception as e:
                self.update_results(f"│ Error: {str(e):<71} │\n")
            self.update_results("└" + "─" * 78 + "┘\n\n")

        # Decode MC_MISC3 if available
        if mc_misc3:
            self.update_results("┌─ MC_MISC3 DECODE " + "─" * 60 + "┐\n")
            try:
                src_id = dec.cha_decoder(value=mc_misc3, type='SrcID')
                ismq = dec.cha_decoder(value=mc_misc3, type='ISMQ')
                attribute = dec.cha_decoder(value=mc_misc3, type='Attribute')
                result = dec.cha_decoder(value=mc_misc3, type='Result')
                local_port = dec.cha_decoder(value=mc_misc3, type='Local Port')

                self.update_results(f"│ Source ID:         {src_id:<57} │\n")
                self.update_results(f"│ ISMQ FSM:          {ismq:<57} │\n")
                self.update_results(f"│ SAD Attribute:     {attribute:<57} │\n")
                self.update_results(f"│ SAD Result:        {result:<57} │\n")
                self.update_results(f"│ Local Port:        {local_port:<57} │\n")
            except Exception as e:
                self.update_results(f"│ Error: {str(e):<71} │\n")
            self.update_results("└" + "─" * 78 + "┘\n\n")

        self.update_results("✓ Decode Complete\n")

    def decode_llc(self, values, product):
        """Decode LLC MCA registers"""
        if product == 'DMR':
            self.update_results("Note: DMR uses CCF decoder (includes LLC). Use CHA/CCF decoder.\n")
            return

        self.update_results("╔" + "═" * 78 + "╗\n")
        self.update_results(f"║ LLC MCA DECODE - {product:<66} ║\n")
        self.update_results("╚" + "═" * 78 + "╝\n\n")

        mc_status = values.get('MC_STATUS', '')
        mc_addr = values.get('MC_ADDR', '')
        mc_misc = values.get('MC_MISC', '')

        # Display raw values
        self.update_results("Raw Register Values:\n")
        self.update_results("-" * 40 + "\n")
        self.update_results(f"  MC_STATUS:  {mc_status}\n")
        if mc_addr:
            self.update_results(f"  MC_ADDR:    {mc_addr}\n")
        if mc_misc:
            self.update_results(f"  MC_MISC:    {mc_misc}\n")
        self.update_results("\n")

        # Create decoder instance
        import pandas as pd
        dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
        dec = mcparse.decoder(data=dummy_df, product=product)

        # Decode MC_STATUS
        self.update_results("MC_STATUS Decode:\n")
        self.update_results("-" * 40 + "\n")

        try:
            # MSCOD decode
            mscod = dec.llc_decoder(value=mc_status, type='MC DECODE')
            self.update_results(f"  MSCOD (Error Type):  {mscod}\n")

            # MiscV
            miscv = dec.llc_decoder(value=mc_status, type='MiscV')
            self.update_results(f"  MISCV:               {miscv}\n")

            # Standard status bits
            val_bit = self.extract_bits(mc_status, 63, 63)
            uc_bit = self.extract_bits(mc_status, 61, 61)
            pcc_bit = self.extract_bits(mc_status, 57, 57)

            self.update_results(f"  VAL (Valid):         {val_bit}\n")
            self.update_results(f"  UC (Uncorrected):    {uc_bit}\n")
            self.update_results(f"  PCC (Proc Context):  {pcc_bit}\n")

        except Exception as e:
            self.update_results(f"  Error decoding MC_STATUS: {str(e)}\n")

        self.update_results("\n")

        # Decode MC_MISC if available
        if mc_misc:
            self.update_results("MC_MISC Decode:\n")
            self.update_results("-" * 40 + "\n")
            try:
                rsf = dec.llc_decoder(value=mc_misc, type='RSF')
                lsf = dec.llc_decoder(value=mc_misc, type='LSF')
                llc_misc = dec.llc_decoder(value=mc_misc, type='LLC_misc')

                self.update_results(f"  RSF:               {rsf}\n")
                self.update_results(f"  LSF:               {lsf}\n")
                self.update_results(f"  LLC_MISC:          {llc_misc}\n")
            except Exception as e:
                self.update_results(f"  Error decoding MC_MISC: {str(e)}\n")
            self.update_results("\n")

        self.update_results("=" * 80 + "\n")
        self.update_results("Decode Complete\n")

    def decode_core(self, values, product):
        """Decode CORE MCA registers using selected bank type"""
        bank_type = self.subtype_var.get()

        self.update_results("=" * 80 + "\n")
        self.update_results(f"CORE MCA DECODE - {product} - {bank_type}\n")
        self.update_results("=" * 80 + "\n\n")

        mc_status = values.get('MC_STATUS', '')
        mc_addr = values.get('MC_ADDR', '')
        mc_misc = values.get('MC_MISC', '')

        # Display raw values
        self.update_results("Raw Register Values:\n")
        self.update_results("-" * 40 + "\n")
        self.update_results(f"  MC_STATUS:  {mc_status}\n")
        if mc_addr:
            self.update_results(f"  MC_ADDR:    {mc_addr}\n")
        if mc_misc:
            self.update_results(f"  MC_MISC:    {mc_misc}\n")
        self.update_results("\n")

        # Create decoder instance
        import pandas as pd
        dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
        dec = mcparse.decoder(data=dummy_df, product=product)

        self.update_results(f"MC_STATUS Decode ({bank_type}):\n")
        self.update_results("-" * 40 + "\n")

        try:
            mcacod, mscod = dec.core_decoder(value=mc_status, type=bank_type)

            self.update_results(f"  Bank Type:              {bank_type}\n")
            self.update_results(f"  MCACOD (Error Decode):  {mcacod}\n")
            self.update_results(f"  MSCOD:                  {mscod}\n")

            # Standard status bits
            val_bit = extract_bits(mc_status, 63, 63)
            uc_bit = extract_bits(mc_status, 61, 61)
            pcc_bit = extract_bits(mc_status, 57, 57)

            self.update_results(f"  VAL (Valid):            {val_bit}\n")
            self.update_results(f"  UC (Uncorrected):       {uc_bit}\n")
            self.update_results(f"  PCC (Proc Context):     {pcc_bit}\n")

        except Exception as e:
            self.update_results(f"  Error decoding MC_STATUS: {str(e)}\n")

        self.update_results("\n")
        self.update_results("=" * 80 + "\n")
        self.update_results("Decode Complete\n")

    def detect_core_bank(self, mscod, product):
        """Auto-detect core bank type from MSCOD value"""
        # For BigCore products (GNR, DMR)
        if product in ['GNR', 'DMR']:
            # ML2 typically has MSCOD in range 0x00-0x7F
            if mscod <= 0x7F:
                return 'ML2'
            # DCU typically has specific MSCOD patterns
            elif mscod <= 0x1F:
                return 'DCU'
            # IFU has MSCOD up to 0x1FFF
            elif mscod <= 0x1FFF:
                return 'IFU'
            # DTLB has MSCOD up to 0x3F
            elif mscod <= 0x3F:
                return 'DTLB'
            else:
                return 'ML2'  # Default to ML2

        # For AtomCore products (CWF)
        elif product == 'CWF':
            # Default to L2 for Atom
            return 'L2'

        return 'ML2'  # Ultimate fallback

    def decode_memory(self, values, product):
        """Decode Memory Subsystem MCA registers"""
        mem_type = self.subtype_var.get()

        self.update_results("=" * 80 + "\n")
        self.update_results(f"MEMORY MCA DECODE - {product} - {mem_type}\n")
        self.update_results("=" * 80 + "\n\n")

        mc_status = values.get('MC_STATUS', '')
        mc_addr = values.get('MC_ADDR', '')
        mc_misc = values.get('MC_MISC', '')

        # Display raw values
        self.update_results("Raw Register Values:\n")
        self.update_results("-" * 40 + "\n")
        self.update_results(f"  MC_STATUS:  {mc_status}\n")
        if mc_addr:
            self.update_results(f"  MC_ADDR:    {mc_addr}\n")
        if mc_misc:
            self.update_results(f"  MC_MISC:    {mc_misc}\n")
        self.update_results("\n")

        # Create decoder instance
        import pandas as pd
        dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
        dec = mcparse.decoder(data=dummy_df, product=product)

        # Decode based on memory type
        self.update_results(f"MC_STATUS Decode ({mem_type}):\n")
        self.update_results("-" * 40 + "\n")

        try:
            decoded = dec.mem_decoder(value=mc_status, instance_type=mem_type)

            self.update_results(f"  Decoded Value:  {decoded}\n")

            # Standard status bits
            val_bit = extract_bits(mc_status, 63, 63)
            uc_bit = extract_bits(mc_status, 61, 61)
            pcc_bit = extract_bits(mc_status, 57, 57)

            self.update_results(f"  VAL (Valid):         {val_bit}\n")
            self.update_results(f"  UC (Uncorrected):    {uc_bit}\n")
            self.update_results(f"  PCC (Proc Context):  {pcc_bit}\n")

        except Exception as e:
            self.update_results(f"  Error decoding MC_STATUS: {str(e)}\n")
            # Try generic decode if specific fails
            self.update_results("\n  Attempting generic decode...\n")
            try:
                mscod = extract_bits(mc_status, 16, 31)
                mcacod = extract_bits(mc_status, 0, 15)
                self.update_results(f"  MSCOD (bits 16-31):  0x{mscod:04X}\n")
                self.update_results(f"  MCACOD (bits 0-15):  0x{mcacod:04X}\n")
            except:
                pass

        self.update_results("\n")
        self.update_results("=" * 80 + "\n")
        self.update_results("Decode Complete\n")

    def extract_bits(self, hex_value, min_bit, max_bit):
        """Extract specific bits from a hex value"""
        if isinstance(hex_value, str):
            value = int(hex_value, 16)
        else:
            value = hex_value

        # Create mask
        num_bits = max_bit - min_bit + 1
        mask = (1 << num_bits) - 1

        # Extract bits
        extracted = (value >> min_bit) & mask

        return extracted

    def decode_io(self, values, product):
        """Decode IO Subsystem MCA registers"""
        io_type = self.subtype_var.get()

        self.update_results("=" * 80 + "\n")
        self.update_results(f"IO MCA DECODE - {product} - {io_type}\n")
        self.update_results("=" * 80 + "\n\n")

        mc_status = values.get('MC_STATUS', '')
        mc_addr = values.get('MC_ADDR', '')
        mc_misc = values.get('MC_MISC', '')

        # Display raw values
        self.update_results("Raw Register Values:\n")
        self.update_results("-" * 40 + "\n")
        self.update_results(f"  MC_STATUS:  {mc_status}\n")
        if mc_addr:
            self.update_results(f"  MC_ADDR:    {mc_addr}\n")
        if mc_misc:
            self.update_results(f"  MC_MISC:    {mc_misc}\n")
        self.update_results("\n")

        # Create decoder instance
        import pandas as pd
        dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
        dec = mcparse.decoder(data=dummy_df, product=product)

        # Decode based on IO type
        self.update_results(f"MC_STATUS Decode ({io_type}):\n")
        self.update_results("-" * 40 + "\n")

        try:
            mcacod_decoded, mscod_decoded = dec.io_decoder(value=mc_status, instance_type=io_type)

            self.update_results(f"  MCACOD:  {mcacod_decoded}\n")
            self.update_results(f"  MSCOD:   {mscod_decoded}\n")

            # Standard status bits
            val_bit = extract_bits(mc_status, 63, 63)
            uc_bit = extract_bits(mc_status, 61, 61)
            pcc_bit = extract_bits(mc_status, 57, 57)

            self.update_results(f"  VAL (Valid):         {val_bit}\n")
            self.update_results(f"  UC (Uncorrected):    {uc_bit}\n")
            self.update_results(f"  PCC (Proc Context):  {pcc_bit}\n")

        except Exception as e:
            self.update_results(f"  Error decoding MC_STATUS: {str(e)}\n")

        self.update_results("\n")
        self.update_results("=" * 80 + "\n")
        self.update_results("Decode Complete\n")

    def decode_first_error(self, values, product):
        """Decode First Error Logger - UBOX MCERR/IERR Logging registers"""
        self.update_results("=" * 80 + "\n")
        self.update_results(f"FIRST ERROR DECODE - {product}\n")
        self.update_results("=" * 80 + "\n\n")

        mcerr_reg = values.get('MCERRLOGGINGREG', '')
        ierr_reg = values.get('IERRLOGGINGREG', '')

        # Display raw values
        self.update_results("Raw Register Values:\n")
        self.update_results("-" * 40 + "\n")
        if mcerr_reg:
            self.update_results(f"  MCERRLOGGINGREG:  {mcerr_reg}\n")
        if ierr_reg:
            self.update_results(f"  IERRLOGGINGREG:   {ierr_reg}\n")
        self.update_results("\n")

        # Create decoder instance
        import pandas as pd
        dummy_df = pd.DataFrame({'VisualId': [1], 'TestName': ['dummy'], 'TestValue': ['0x0']})
        dec = mcparse.decoder(data=dummy_df, product=product)

        # Define the field names for portid decoder output
        portid_data = ['FirstError - DIEID', 'FirstError - PortID', 'FirstError - Location',
                      'FirstError - FromCore', 'SecondError - DIEID', 'SecondError - PortID',
                      'SecondError - Location', 'SecondError - FromCore']

        # Decode MCERR if provided
        if mcerr_reg:
            self.update_results("MCERRLOGGINGREG Decode:\n")
            self.update_results("-" * 40 + "\n")
            try:
                portids_values = dec.portids_decoder(value=mcerr_reg, portid_data=portid_data, event='mcerr')

                self.update_results(f"  First Error:\n")
                self.update_results(f"    DIE ID:     {portids_values.get('FirstError - DIEID', 'N/A')}\n")
                self.update_results(f"    Port ID:    {portids_values.get('FirstError - PortID', 'N/A')}\n")
                self.update_results(f"    Location:   {portids_values.get('FirstError - Location', 'N/A')}\n")
                self.update_results(f"    From Core:  {portids_values.get('FirstError - FromCore', 'N/A')}\n")

                self.update_results(f"\n  Second Error:\n")
                self.update_results(f"    DIE ID:     {portids_values.get('SecondError - DIEID', 'N/A')}\n")
                self.update_results(f"    Port ID:    {portids_values.get('SecondError - PortID', 'N/A')}\n")
                self.update_results(f"    Location:   {portids_values.get('SecondError - Location', 'N/A')}\n")
                self.update_results(f"    From Core:  {portids_values.get('SecondError - FromCore', 'N/A')}\n")

            except Exception as e:
                self.update_results(f"  Error decoding MCERRLOGGINGREG: {str(e)}\n")

            self.update_results("\n")

        # Decode IERR if provided
        if ierr_reg:
            self.update_results("IERRLOGGINGREG Decode:\n")
            self.update_results("-" * 40 + "\n")
            try:
                portids_values = dec.portids_decoder(value=ierr_reg, portid_data=portid_data, event='ierr')

                self.update_results(f"  First Error:\n")
                self.update_results(f"    DIE ID:     {portids_values.get('FirstError - DIEID', 'N/A')}\n")
                self.update_results(f"    Port ID:    {portids_values.get('FirstError - PortID', 'N/A')}\n")
                self.update_results(f"    Location:   {portids_values.get('FirstError - Location', 'N/A')}\n")
                self.update_results(f"    From Core:  {portids_values.get('FirstError - FromCore', 'N/A')}\n")

                self.update_results(f"\n  Second Error:\n")
                self.update_results(f"    DIE ID:     {portids_values.get('SecondError - DIEID', 'N/A')}\n")
                self.update_results(f"    Port ID:    {portids_values.get('SecondError - PortID', 'N/A')}\n")
                self.update_results(f"    Location:   {portids_values.get('SecondError - Location', 'N/A')}\n")
                self.update_results(f"    From Core:  {portids_values.get('SecondError - FromCore', 'N/A')}\n")

            except Exception as e:
                self.update_results(f"  Error decoding IERRLOGGINGREG: {str(e)}\n")

            self.update_results("\n")

        self.update_results("=" * 80 + "\n")
        self.update_results("Decode Complete\n")

    def update_results(self, text, clear=False):
        """Update results text area"""
        if clear:
            self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)

    def copy_results(self):
        """Copy decoded results to clipboard"""
        try:
            results = self.results_text.get(1.0, tk.END).strip()
            if results:
                self.root.clipboard_clear()
                self.root.clipboard_append(results)
                self.root.update()
                messagebox.showinfo("Success", "Results copied to clipboard!")
            else:
                messagebox.showwarning("Warning", "No results to copy!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {str(e)}")

    def clear_all(self):
        """Clear all input fields and results"""
        for entry in self.register_entries.values():
            entry.delete(0, tk.END)
        self.update_results("", clear=True)


def start_mca_decoder():
    """Launch the MCA Decoder GUI"""
    root = tk.Tk()
    app = MCADecoderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    start_mca_decoder()
