import tkinter as tk
from functools import partial

class SystemMaskEditor:
    def __init__(self, compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = 'GNR', callback=None):
        self.compute0_core_hex = compute0_core_hex
        self.compute0_cha_hex = compute0_cha_hex
        self.compute1_core_hex = compute1_core_hex
        self.compute1_cha_hex = compute1_cha_hex
        self.compute2_core_hex = compute2_core_hex
        self.compute2_cha_hex = compute2_cha_hex
        self.root = None
        self.product = product
        self.callback = callback

        if 'CWF' in product:
            self.disabled_rows = [0, 1, 2, 3]
            self.disabled_cols = [0,10]
            self.corebtname = 'MODULE'   
        else:
            self.disabled_rows = [2, 3]
            self.disabled_cols = [0, 10]
            self.corebtname = 'CORE'         
        ## Init returning variable
        self.masks =  {
        "ia_compute_0": compute0_core_hex,
        "ia_compute_1": compute1_core_hex,
        "ia_compute_2": compute2_core_hex,
        "llc_compute_0": compute0_cha_hex,
        "llc_compute_1": compute1_cha_hex,
        "llc_compute_2": compute2_cha_hex
        }

    # Convert hex string to bit string
    def hex_to_bit_string(self, hex_str):
        #print(hex_str, type(hex_str))
        if isinstance(hex_str, int):
            return bin(hex_str)[2:].zfill(num_of_bits)[::-1]
        scale = 16  # base of hexadecimal
        num_of_bits = 60  # number of bits in the bitstring
        return bin(int(hex_str, scale))[2:].zfill(num_of_bits)[::-1]  # Reverse the bit string

    # Convert bit string to hex string
    def bit_string_to_hex(self, bit_string):
        num_of_bits = 60  # number of bits in the bitstring
        hex_str = hex(int("".join(bit_string)[::-1], 2))[2:].zfill(num_of_bits // 4)
        return "0x" + hex_str

    def create_interface(self, root, core_hex, cha_hex, title, cdie, callback):
        # Initialize 60-bit strings
        core_bit_string = list(self.hex_to_bit_string(core_hex))
        cha_bit_string = list(self.hex_to_bit_string(cha_hex))

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
        top_label.grid(row=0, column=1, columnspan=11)

        # Add row and column labels
        for i in range(7):
            tk.Label(interface_root, text=f"ROW {i}", borderwidth=2, relief="solid", font=("Helvetica", 10)).grid(row=i*2+1, column=0, rowspan=2, sticky="nsew")
        for j in range(10):
            tk.Label(interface_root, text=f"COL {j}", borderwidth=2, relief="solid", font=("Helvetica", 10)).grid(row=15, column=j+1, sticky="nsew")

        # Create 7x10 grid of buttons
        buttons = []
        core_bit_index = 0
        cha_bit_index = 0
        for j in range(10):
            for i in range(7):
                if (i in [2, 3, 4, 5, 6] and j in [0, 9]):
                    if i == 4 and j == 0:
                        label = "MC2"
                    elif i == 5 and j == 0:
                        label = "MC3"
                    elif i == 6 and j == 0:
                        label = "SPK0"
                    elif i == 4 and j == 9:
                        label = "MC0"
                    elif i == 5 and j == 9:
                        label = "MC1"
                    elif i == 6 and j == 9:
                        label = "SPK1"
                    else:
                        label = "DISABLED"
                    btn_core = tk.Button(interface_root, text=label, width=10, height=2, bg="gray", state="disabled", borderwidth=2, relief="solid", font=("Helvetica", 7, "bold"))
                    btn_cha = tk.Button(interface_root, text=label, width=10, height=2, bg="gray", state="disabled", borderwidth=2, relief="solid", font=("Helvetica", 7, "bold"))
                elif (i in self.disabled_rows and j in range(self.disabled_cols[0], self.disabled_cols[-1])):
                    btn_core = create_button(interface_root, core_bit_index, f"{self.corebtname} {core_bit_index + (cdie*60)}", core_bit_string)
                    btn_cha = create_button(interface_root, cha_bit_index, f"CHA {cha_bit_index + (cdie*60)}", cha_bit_string)
                    btn_core.config(bg="gray", state="disabled")
                    btn_cha.config(bg="gray", state="disabled")
                    core_bit_index += 1
                    cha_bit_index += 1
                else:
                    btn_core = create_button(interface_root, core_bit_index, f"{self.corebtname} {core_bit_index + (cdie*60)}", core_bit_string)
                    btn_cha = create_button(interface_root, cha_bit_index, f"CHA {cha_bit_index + (cdie*60)}", cha_bit_string)
                    core_bit_index += 1
                    cha_bit_index += 1
                btn_core.grid(row=i*2+1, column=j+1, padx=1, pady=1, sticky="nsew")
                btn_cha.grid(row=i*2+2, column=j+1, padx=1, pady=1, sticky="nsew")
                buttons.append((btn_core, btn_cha))

        # Add save button
        def save_hex_strings():
            new_core_hex = self.bit_string_to_hex(core_bit_string)
            new_cha_hex = self.bit_string_to_hex(cha_bit_string)
            print(f"New {self.corebtname} Hex: {new_core_hex}")
            print(f"New CHA Hex: {new_cha_hex}")
            interface_root.destroy()
            callback(new_core_hex, new_cha_hex)

        save_button = tk.Button(interface_root, text="Save", command=save_hex_strings)
        save_button.grid(row=16, column=5, columnspan=2, pady=10)

    def on_save(self, compute, core, cha):
        if compute == 0:
            self.compute0_core_hex = core
            self.compute0_cha_hex = cha
        elif compute == 1:
            self.compute1_core_hex = core
            self.compute1_cha_hex = cha
        elif compute == 2:
            self.compute2_core_hex = core
            self.compute2_cha_hex = cha

    def start(self, root):
        # Create main application window
        self.root = root if root != None else tk.Tk()
        self.root.title("System Mask Edit")

        # Create a frame for the buttons
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(pady=20)

        # Create title label
        title_label = tk.Label(frame, text="System Mask Edit", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Create buttons for Compute0, Compute1, and Compute2
        compute0_button = tk.Button(frame, text="Compute0", width=15, height=2, command=partial(self.create_interface, self.root, self.compute0_core_hex, self.compute0_cha_hex, "Compute0 Interface", 0,partial(self.on_save, 0)))
        compute0_button.grid(row=1, column=0, padx=10, pady=10)

        if self.compute1_cha_hex != None: # Only checking CHA, no need for both checks of CHA and CORE
            compute1_button = tk.Button(frame, text="Compute1", width=15, height=2, command=partial(self.create_interface, self.root, self.compute1_core_hex, self.compute1_cha_hex, "Compute1 Interface",1,  partial(self.on_save, 1)))
            compute1_button.grid(row=1, column=1, padx=10, pady=10)

        if self.compute2_cha_hex != None: # Only checking CHA, no need for both checks of CHA and CORE
            compute2_button = tk.Button(frame, text="Compute2", width=15, height=2, command=partial(self.create_interface, self.root, self.compute2_core_hex, self.compute2_cha_hex, "Compute2 Interface",2, partial(self.on_save, 2)))
            compute2_button.grid(row=1, column=2, padx=10, pady=10)

        # Add Save and Cancel buttons in the same row
        save_button = tk.Button(frame, text="Save All", width=15, height=2, command=self.save_all)
        save_button.grid(row=2, column=1, padx=10, pady=10)

        cancel_button = tk.Button(frame, text="Cancel", width=15, height=2, command=self.cancel)
        cancel_button.grid(row=2, column=2, padx=10, pady=10)

        # Run the main event loop
        self.root.mainloop()

        #return self.compute0_core_hex, self.compute0_cha_hex, self.compute1_core_hex, self.compute1_cha_hex, self.compute2_core_hex, self.compute2_cha_hex
        return self.masks
    
    def save_all(self):
        self.masks =  {
        "ia_compute_0": self.compute0_core_hex,
        "ia_compute_1": self.compute1_core_hex,
        "ia_compute_2": self.compute2_core_hex,
        "llc_compute_0": self.compute0_cha_hex,
        "llc_compute_1": self.compute1_cha_hex,
        "llc_compute_2": self.compute2_cha_hex
    }
        if self.callback:
            self.callback(self.masks)  # Use callback to pass data back        
        self.root.destroy()

    def cancel(self):
        #self.masks = None
        self.root.destroy()

def Masking(root, compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product, callback):
    # Create an instance of SystemMaskEditor
    editor = SystemMaskEditor(compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product=product, callback=callback)

    # Start the UI
    masks = editor.start(root)

    print("Updated hex values:")
    print("Compute0 Core:", masks["ia_compute_0"])
    print("Compute0 CHA:", masks["llc_compute_0"])
    print("Compute1 Core:", masks["ia_compute_1"])
    print("Compute1 CHA:", masks["llc_compute_1"])
    print("Compute2 Core:", masks["ia_compute_2"])
    print("Compute2 CHA:", masks["llc_compute_2"])

    return masks

def test_UI(root):
    # Example hex values for Compute0, Compute1, and Compute2
    compute0_core_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"
    compute0_cha_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"

    compute1_core_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"
    compute1_cha_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"

    compute2_core_hex ="0x0000000000000000000000000000000000000000000000000000000000000000"
    compute2_cha_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"

    # Create an instance of SystemMaskEditor
    editor = SystemMaskEditor(compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product='GNR')

    # Start the UI
    masks = editor.start(root)

    print("Updated hex values:")
    print("Compute0 Core:", masks["ia_compute_0"])
    print("Compute0 CHA:", masks["llc_compute_0"])
    print("Compute1 Core:", masks["ia_compute_1"])
    print("Compute1 CHA:", masks["llc_compute_1"])
    print("Compute2 Core:", masks["ia_compute_2"])
    print("Compute2 CHA:", masks["llc_compute_2"])
    
if __name__ == "__main__":
        
    root = tk.Tk()
    #root.title("System Mask Edit")
    test_UI(root)