import tkinter as tk
from functools import partial

class SystemMaskEditor:
    def __init__(self, cbb0_core_hex, cbb0_llc_hex, cbb1_core_hex=None, cbb1_llc_hex=None,
                 cbb2_core_hex=None, cbb2_llc_hex=None, cbb3_core_hex=None, cbb3_llc_hex=None,
                 product='DMR', callback=None):
        # CBB-based masks (32 bits per CBB)
        self.cbb0_core_hex = cbb0_core_hex
        self.cbb0_llc_hex = cbb0_llc_hex
        self.cbb1_core_hex = cbb1_core_hex
        self.cbb1_llc_hex = cbb1_llc_hex
        self.cbb2_core_hex = cbb2_core_hex
        self.cbb2_llc_hex = cbb2_llc_hex
        self.cbb3_core_hex = cbb3_core_hex
        self.cbb3_llc_hex = cbb3_llc_hex
        self.root = None
        self.product = product
        self.callback = callback

        # DMR uses MODULE naming
        if 'DMR' in product or 'CWF' in product:
            self.disabled_rows = []  # No disabled rows for DMR
            self.disabled_cols = []  # No disabled columns
            self.corebtname = 'MODULE'
        else:
            self.disabled_rows = [2, 3]
            self.disabled_cols = [0, 10]
            self.corebtname = 'CORE'

        # Initialize returning variable with CBB-based keys
        self.masks = {
            "ia_cbb0": cbb0_core_hex,
            "ia_cbb1": cbb1_core_hex,
            "ia_cbb2": cbb2_core_hex,
            "ia_cbb3": cbb3_core_hex,
            "llc_cbb0": cbb0_llc_hex,
            "llc_cbb1": cbb1_llc_hex,
            "llc_cbb2": cbb2_llc_hex,
            "llc_cbb3": cbb3_llc_hex
        }

    # Convert hex string to bit string (32 bits for DMR CBB)
    def hex_to_bit_string(self, hex_str) -> str:
        scale = 16  # base of hexadecimal
        num_of_bits = 32  # DMR: 32 bits per CBB
        if isinstance(hex_str, int):
            return bin(hex_str)[2:].zfill(num_of_bits)[::-1]
        return bin(int(hex_str, scale))[2:].zfill(num_of_bits)[::-1]  # Reverse the bit string

    # Convert bit string to hex string (32 bits for DMR CBB)
    def bit_string_to_hex(self, bit_string) -> str:
        num_of_bits = 32  # DMR: 32 bits per CBB
        hex_str = hex(int("".join(bit_string)[::-1], 2))[2:].zfill(num_of_bits // 4)
        return "0x" + hex_str

    def create_interface(self, root, core_hex, llc_hex, title, cbb_id, callback) -> None:
        # Initialize 32-bit strings (DMR: 32 modules/LLC per CBB)
        core_bit_string = list(self.hex_to_bit_string(core_hex))
        llc_bit_string = list(self.hex_to_bit_string(llc_hex))

        def toggle_button(button, index, bit_string):
            if bit_string[index] == "0":
                button.config(bg="red")
                bit_string[index] = "1"
            else:
                button.config(bg="green")
                bit_string[index] = "0"
            print("".join(bit_string))

        def create_button(root, index, text, bit_string):
            state = "normal"
            bg = "green"
            fg = "white"
            if bit_string[index] == "1":
                state = "disabled"
                fg = "orange"
            btn = tk.Button(root, text=text, width=10, height=2, bg=bg, fg=fg, state=state,
                            font=("Helvetica", 10, "bold"), command=lambda: toggle_button(btn, index, bit_string))
            if bit_string[index] == "1":
                btn.config(bg="red")
            return btn

        # Create main application window
        interface_root = tk.Toplevel(root)
        interface_root.title(title)

        # Add top label
        top_label = tk.Label(interface_root, text=title, font=("Helvetica", 14, "bold"))
        top_label.grid(row=0, column=1, columnspan=4)

        # Add row and column labels for DMR layout (8 rows × 4 columns)
        for i in range(8):
            tk.Label(interface_root, text=f"ROW{i}", borderwidth=2, relief="solid", font=("Helvetica", 10)).grid(row=i*2+1, column=0, rowspan=2, sticky="nsew")
        for j in range(4):
            tk.Label(interface_root, text=f"COL{j}", borderwidth=2, relief="solid", font=("Helvetica", 10)).grid(row=17, column=j+1, sticky="nsew")

        # DMR tile layout: 8 rows × 4 columns = 32 modules/LLCs
        # Row-first ordering: Row0: 0-3, Row1: 4-7, Row2: 8-11, etc.
        # This matches the physical layout where modules are numbered left-to-right, top-to-bottom

        buttons = []
        core_bit_index = 0
        llc_bit_index = 0

        for i in range(8):  # 8 rows
            for j in range(4):  # 4 columns (DCM0-DCM3)
                # Calculate module index based on row-first ordering
                module_idx = i * 4 + j  # Row0: 0-3, Row1: 4-7, Row2: 8-11, etc.

                btn_core = create_button(interface_root, module_idx,
                                        f"{self.corebtname} {module_idx + (cbb_id*32)}",
                                        core_bit_string)
                btn_llc = create_button(interface_root, module_idx,
                                       f"CBO {module_idx + (cbb_id*32)}",
                                       llc_bit_string)

                btn_core.grid(row=i*2+1, column=j+1, padx=1, pady=1, sticky="nsew")
                btn_llc.grid(row=i*2+2, column=j+1, padx=1, pady=1, sticky="nsew")
                buttons.append((btn_core, btn_llc))

        # Add save button
        def save_hex_strings():
            new_core_hex = self.bit_string_to_hex(core_bit_string)
            new_llc_hex = self.bit_string_to_hex(llc_bit_string)
            print(f"New {self.corebtname} Hex: {new_core_hex}")
            print(f"New LLC Hex: {new_llc_hex}")
            interface_root.destroy()
            callback(new_core_hex, new_llc_hex)

        save_button = tk.Button(interface_root, text="Save", command=save_hex_strings)
        save_button.grid(row=18, column=2, columnspan=2, pady=10)

    def on_save(self, cbb_id, core, llc) -> None:
        if cbb_id == 0:
            self.cbb0_core_hex = core
            self.cbb0_llc_hex = llc
        elif cbb_id == 1:
            self.cbb1_core_hex = core
            self.cbb1_llc_hex = llc
        elif cbb_id == 2:
            self.cbb2_core_hex = core
            self.cbb2_llc_hex = llc
        elif cbb_id == 3:
            self.cbb3_core_hex = core
            self.cbb3_llc_hex = llc

    def start(self, root):
        # Create main application window
        self.root = root if root != None else tk.Tk()
        self.root.title("System Mask Edit - DMR CBB Configuration")

        # Create a frame for the buttons
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(pady=20)

        # Create title label
        title_label = tk.Label(frame, text="DMR CBB Mask Editor", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Create buttons for CBB0, CBB1, CBB2, and CBB3
        cbb0_button = tk.Button(frame, text="CBB0", width=15, height=2,
                               command=partial(self.create_interface, self.root,
                                             self.cbb0_core_hex, self.cbb0_llc_hex,
                                             "CBB0 Interface", 0, partial(self.on_save, 0)))
        cbb0_button.grid(row=1, column=0, padx=10, pady=10)

        if self.cbb1_llc_hex is not None:
            cbb1_button = tk.Button(frame, text="CBB1", width=15, height=2,
                                   command=partial(self.create_interface, self.root,
                                                 self.cbb1_core_hex, self.cbb1_llc_hex,
                                                 "CBB1 Interface", 1, partial(self.on_save, 1)))
            cbb1_button.grid(row=1, column=1, padx=10, pady=10)

        if self.cbb2_llc_hex is not None:
            cbb2_button = tk.Button(frame, text="CBB2", width=15, height=2,
                                   command=partial(self.create_interface, self.root,
                                                 self.cbb2_core_hex, self.cbb2_llc_hex,
                                                 "CBB2 Interface", 2, partial(self.on_save, 2)))
            cbb2_button.grid(row=1, column=2, padx=10, pady=10)

        if self.cbb3_llc_hex is not None:
            cbb3_button = tk.Button(frame, text="CBB3", width=15, height=2,
                                   command=partial(self.create_interface, self.root,
                                                 self.cbb3_core_hex, self.cbb3_llc_hex,
                                                 "CBB3 Interface", 3, partial(self.on_save, 3)))
            cbb3_button.grid(row=1, column=3, padx=10, pady=10)

        # Add Save and Cancel buttons in the same row
        save_button = tk.Button(frame, text="Save All", width=15, height=2, command=self.save_all)
        save_button.grid(row=2, column=1, padx=10, pady=10)

        cancel_button = tk.Button(frame, text="Cancel", width=15, height=2, command=self.cancel)
        cancel_button.grid(row=2, column=2, padx=10, pady=10)

        # Run the main event loop
        self.root.mainloop()

        return self.masks

    def save_all(self) -> None:
        self.masks = {
            "ia_cbb0": self.cbb0_core_hex,
            "ia_cbb1": self.cbb1_core_hex,
            "ia_cbb2": self.cbb2_core_hex,
            "ia_cbb3": self.cbb3_core_hex,
            "llc_cbb0": self.cbb0_llc_hex,
            "llc_cbb1": self.cbb1_llc_hex,
            "llc_cbb2": self.cbb2_llc_hex,
            "llc_cbb3": self.cbb3_llc_hex
        }
        if self.callback:
            self.callback(self.masks)  # Use callback to pass data back
        self.root.destroy()

    def cancel(self) -> None:
        #self.masks = None
        self.root.destroy()

def Masking(root, cbb0_core_hex, cbb0_llc_hex, cbb1_core_hex=None, cbb1_llc_hex=None,
            cbb2_core_hex=None, cbb2_llc_hex=None, cbb3_core_hex=None, cbb3_llc_hex=None,
            product='DMR', callback=None):
    """
    DMR Masking function with CBB-based configuration.

    Args:
        root: Tkinter root window
        cbb0_core_hex: CBB0 module mask (32-bit hex string)
        cbb0_llc_hex: CBB0 LLC mask (32-bit hex string)
        cbb1_core_hex: CBB1 module mask (optional)
        cbb1_llc_hex: CBB1 LLC mask (optional)
        cbb2_core_hex: CBB2 module mask (optional)
        cbb2_llc_hex: CBB2 LLC mask (optional)
        cbb3_core_hex: CBB3 module mask (optional)
        cbb3_llc_hex: CBB3 LLC mask (optional)
        product: Product name (default 'DMR')
        callback: Callback function for mask updates

    Returns:
        Dictionary with keys: ia_cbb0-3, llc_cbb0-3
    """
    # Create an instance of SystemMaskEditor
    editor = SystemMaskEditor(cbb0_core_hex, cbb0_llc_hex, cbb1_core_hex, cbb1_llc_hex,
                             cbb2_core_hex, cbb2_llc_hex, cbb3_core_hex, cbb3_llc_hex,
                             product=product, callback=callback)

    # Start the UI
    masks = editor.start(root)

    print("Updated hex values:")
    print("CBB0 Module:", masks["ia_cbb0"])
    print("CBB0 LLC:", masks["llc_cbb0"])
    print("CBB1 Module:", masks["ia_cbb1"])
    print("CBB1 LLC:", masks["llc_cbb1"])
    print("CBB2 Module:", masks["ia_cbb2"])
    print("CBB2 LLC:", masks["llc_cbb2"])
    print("CBB3 Module:", masks["ia_cbb3"])
    print("CBB3 LLC:", masks["llc_cbb3"])

    return masks

def test_UI(root) -> None:
    """Test function for DMR CBB-based mask editor"""
    # Example hex values for CBB0-3 (32 bits = 8 hex chars each)
    cbb0_core_hex = "0x00000000"
    cbb0_llc_hex = "0x00000000"

    cbb1_core_hex = "0x00000000"
    cbb1_llc_hex = "0x00000000"

    cbb2_core_hex = "0x00000000"
    cbb2_llc_hex = "0x00000000"

    cbb3_core_hex = "0x00000000"
    cbb3_llc_hex = "0x00000000"

    # Create an instance of SystemMaskEditor
    editor = SystemMaskEditor(cbb0_core_hex, cbb0_llc_hex, cbb1_core_hex, cbb1_llc_hex,
                             cbb2_core_hex, cbb2_llc_hex, cbb3_core_hex, cbb3_llc_hex,
                             product='DMR')

    # Start the UI
    masks = editor.start(root)

    print("Updated hex values:")
    print("CBB0 Module:", masks["ia_cbb0"])
    print("CBB0 LLC:", masks["llc_cbb0"])
    print("CBB1 Module:", masks["ia_cbb1"])
    print("CBB1 LLC:", masks["llc_cbb1"])
    print("CBB2 Module:", masks["ia_cbb2"])
    print("CBB2 LLC:", masks["llc_cbb2"])
    print("CBB3 Module:", masks["ia_cbb3"])
    print("CBB3 LLC:", masks["llc_cbb3"])

if __name__ == "__main__":

    root = tk.Tk()
    #root.title("System Mask Edit")
    test_UI(root)
