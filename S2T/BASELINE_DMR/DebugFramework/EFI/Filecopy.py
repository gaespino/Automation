import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def copy_files(source_dir, dest_dir, file_type=None, keywords=None):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file_type and not file.endswith(file_type):
                continue

            if keywords and not any(keyword in file for keyword in keywords):
                continue

            source_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            shutil.copy2(source_file, dest_file)
            print(f"Copied: {source_file} to {dest_file}")

def browse_source():
    source_path.set(filedialog.askdirectory())

def browse_destination():
    destination_path.set(filedialog.askdirectory())

def start_copy():
    source = source_path.get()
    destination = destination_path.get()
    file_ext = file_extension.get()
    keywords = keyword_entry.get().split(',')

    if not source or not destination:
        messagebox.showerror("Error", "Please select both source and destination directories.")
        return

    copy_files(source, destination, file_ext, keywords)
    messagebox.showinfo("Success", "Files copied successfully!")

# Create the main window
root = tk.Tk()
root.title("File Copy Utility")

# Source directory
source_path = tk.StringVar()
tk.Label(root, text="Source Directory:").grid(row=0, column=0, padx=10, pady=5)
tk.Entry(root, textvariable=source_path, width=50).grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_source).grid(row=0, column=2, padx=10, pady=5)

# Destination directory
destination_path = tk.StringVar()
tk.Label(root, text="Destination Directory:").grid(row=1, column=0, padx=10, pady=5)
tk.Entry(root, textvariable=destination_path, width=50).grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_destination).grid(row=1, column=2, padx=10, pady=5)

# File extension
file_extension = tk.StringVar()
tk.Label(root, text="File Extension:").grid(row=2, column=0, padx=10, pady=5)
tk.Entry(root, textvariable=file_extension, width=20).grid(row=2, column=1, padx=10, pady=5)

# Keywords
tk.Label(root, text="Keywords (comma-separated):").grid(row=3, column=0, padx=10, pady=5)
keyword_entry = tk.Entry(root, width=50)
keyword_entry.grid(row=3, column=1, padx=10, pady=5)

# Start button
tk.Button(root, text="Start Copy", command=start_copy).grid(row=4, column=0, columnspan=3, pady=20)

# Run the application
root.mainloop()