import os
import re
import pandas as pd
from datetime import datetime
from typing import Union, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

class PListSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PList File Search Tool")
        self.root.geometry("850x800")
        self.root.resizable(True, True)
        
        # Variables
        self.folder_path = tk.StringVar()
        self.output_path = tk.StringVar(value=".")
        self.search_type = tk.StringVar(value="exact")
        self.case_sensitive = tk.BooleanVar(value=True)
        self.save_excel = tk.BooleanVar(value=True)
        self.file_filter = tk.StringVar()  # Include filter
        self.exclude_filter = tk.StringVar()  # New exclude filter
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(main_frame, text="PList File Search Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1
        
        # Folder path selection
        ttk.Label(main_frame, text="Search Folder:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.folder_path, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=row, column=2, pady=5)
        row += 1
        
        # Output folder selection
        ttk.Label(main_frame, text="Output Folder:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output_folder).grid(row=row, column=2, pady=5)
        row += 1
        
        # File filtering frame
        filter_frame = ttk.LabelFrame(main_frame, text="File Filtering Options", padding="10")
        filter_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        filter_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Include filter
        ttk.Label(filter_frame, text="Include Files:").grid(row=0, column=0, sticky=tk.W, pady=2)
        include_frame = ttk.Frame(filter_frame)
        include_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        include_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(include_frame, textvariable=self.file_filter, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Label(include_frame, text="(Only search files containing this text - leave blank for all)", 
                 font=('Arial', 8), foreground='gray').grid(row=1, column=0, sticky=tk.W)
        
        # Exclude filter
        ttk.Label(filter_frame, text="Exclude Files:").grid(row=1, column=0, sticky=tk.W, pady=(10, 2))
        exclude_frame = ttk.Frame(filter_frame)
        exclude_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=(10, 2))
        exclude_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(exclude_frame, textvariable=self.exclude_filter, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Label(exclude_frame, text="(Skip files containing any of these terms - separate with commas)", 
                 font=('Arial', 8), foreground='gray').grid(row=1, column=0, sticky=tk.W)
        
        # Search options frame
        options_frame = ttk.LabelFrame(main_frame, text="Search Options", padding="10")
        options_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Search type
        ttk.Label(options_frame, text="Search Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        search_type_frame = ttk.Frame(options_frame)
        search_type_frame.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Radiobutton(search_type_frame, text="Exact Match", variable=self.search_type, value="exact").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(search_type_frame, text="Case Insensitive", variable=self.search_type, value="case_insensitive").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(search_type_frame, text="Regular Expression", variable=self.search_type, value="regex").pack(side=tk.LEFT)
        
        # Save to Excel option
        ttk.Checkbutton(options_frame, text="Save results to Excel", variable=self.save_excel).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Search strings input
        ttk.Label(main_frame, text="Search Strings:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=5)
        ttk.Label(main_frame, text="(Enter one per line or separate with commas)", 
                 font=('Arial', 8), foreground='gray').grid(row=row+1, column=0, columnspan=3, sticky=tk.W)
        row += 2
        
        # Text area for search strings
        self.search_text = scrolledtext.ScrolledText(main_frame, height=8, width=70)
        self.search_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(row, weight=1)
        row += 1
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        self.search_button = ttk.Button(button_frame, text="Search", command=self.start_search, style='Accent.TButton')
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear", command=self.clear_form).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=self.root.quit).pack(side=tk.LEFT)
        row += 1
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to search...")
        self.status_label.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=2)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=10, width=70)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add some example text
        self.search_text.insert('1.0', 'Blender\nScylla\nYakko\nd5022045')
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select folder to search in")
        if folder:
            self.folder_path.set(folder)
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_path.set(folder)
    
    def clear_form(self):
        self.search_text.delete('1.0', tk.END)
        self.results_text.delete('1.0', tk.END)
        self.folder_path.set("")
        self.output_path.set(".")
        self.file_filter.set("")
        self.exclude_filter.set("")
        self.status_label.config(text="Ready to search...")
    
    def get_search_strings(self):
        """Extract search strings from the text area"""
        text = self.search_text.get('1.0', tk.END).strip()
        if not text:
            return []
        
        # Try comma separation first
        if ',' in text:
            strings = [s.strip() for s in text.split(',') if s.strip()]
        else:
            # Use line separation
            strings = [s.strip() for s in text.split('\n') if s.strip()]
        
        return strings
    
    def get_exclude_terms(self):
        """Extract exclude terms from the exclude filter"""
        exclude_text = self.exclude_filter.get().strip()
        if not exclude_text:
            return []
        
        # Split by comma and clean up
        exclude_terms = [term.strip().lower() for term in exclude_text.split(',') if term.strip()]
        return exclude_terms
    
    def should_search_file(self, filename):
        """Check if a file should be searched based on include and exclude filters"""
        filename_lower = filename.lower()
        
        # Check exclude filter first (if any exclude term is found, skip the file)
        exclude_terms = self.get_exclude_terms()
        for exclude_term in exclude_terms:
            if exclude_term in filename_lower:
                return False
        
        # Check include filter
        include_filter = self.file_filter.get().strip()
        if not include_filter:
            return True  # No include filter, so include all (that weren't excluded)
        
        # Check if the filename contains the include filter string
        return include_filter.lower() in filename_lower
    
    def get_filter_description(self):
        """Get a description of the current filters for display"""
        include_filter = self.file_filter.get().strip()
        exclude_terms = self.get_exclude_terms()
        
        descriptions = []
        
        if include_filter:
            descriptions.append(f"including '{include_filter}'")
        
        if exclude_terms:
            if len(exclude_terms) == 1:
                descriptions.append(f"excluding '{exclude_terms[0]}'")
            else:
                descriptions.append(f"excluding {exclude_terms}")
        
        if not descriptions:
            return "all .plist files"
        
        return "files " + " and ".join(descriptions)
    
    def start_search(self):
        """Start the search in a separate thread"""
        # Validate inputs
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder to search in.")
            return
        
        if not os.path.exists(self.folder_path.get()):
            messagebox.showerror("Error", "Selected folder does not exist.")
            return
        
        search_strings = self.get_search_strings()
        if not search_strings:
            messagebox.showerror("Error", "Please enter at least one search string.")
            return
        
        # Disable search button and start progress
        self.search_button.config(state='disabled')
        self.progress.start()
        
        # Update status to show filter info
        filter_desc = self.get_filter_description()
        self.status_label.config(text=f"Searching in {filter_desc}...")
        
        self.results_text.delete('1.0', tk.END)
        
        # Start search in separate thread
        search_thread = threading.Thread(target=self.perform_search, args=(search_strings,))
        search_thread.daemon = True
        search_thread.start()
    
    def perform_search(self, search_strings):
        """Perform the actual search"""
        try:
            folder_path = self.folder_path.get()
            search_type = self.search_type.get()
            
            # Perform search based on type
            if search_type == "exact":
                results = self.search_string_in_plist_files(folder_path, search_strings)
            elif search_type == "case_insensitive":
                results = self.search_string_in_plist_files_case_insensitive(folder_path, search_strings)
            elif search_type == "regex":
                results = self.search_regex_in_plist_files(folder_path, search_strings)
            
            # Update GUI in main thread
            self.root.after(0, self.display_results, results, search_strings)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Search error: {str(e)}")
    
    def display_results(self, results, search_strings):
        """Display search results in the GUI"""
        try:
            # Stop progress bar
            self.progress.stop()
            self.search_button.config(state='normal')
            
            # Convert to DataFrame
            df = self.results_to_dataframe(results)
            
            # Get filter info for display
            filter_desc = self.get_filter_description()
            stats = results.get('_stats', {})
            
            if df.empty:
                self.status_label.config(text=f"No results found in {filter_desc}")
                status_text = f"No matches found for the specified search terms in {filter_desc}."
                if stats:
                    status_text += f"\n\nFiles processed: {stats.get('files_searched', 0)} searched, {stats.get('files_skipped', 0)} skipped"
                self.results_text.insert(tk.END, status_text)
                return
            
            # Display results
            search_display = f"{len(search_strings)} terms" if len(search_strings) > 1 else f"'{search_strings[0]}'"
            self.status_label.config(text=f"Found {len(df)} matches for {search_display} in {filter_desc}")
            
            # Format results for display
            results_text = f"Search Results - Found {len(df)} matches in {filter_desc}\n"
            results_text += "=" * 100 + "\n\n"
            
            # Summary
            results_text += "Summary:\n"
            results_text += f"- Total matches: {len(df)}\n"
            results_text += f"- Unique files: {df['File_Path'].nunique()}\n"
            results_text += f"- Unique PLists: {df['PList_Name'].nunique()}\n"
            results_text += f"- Search terms found: {df['Search_String'].nunique()}\n"
            
            # Filter information
            include_filter = self.file_filter.get().strip()
            exclude_terms = self.get_exclude_terms()
            if include_filter:
                results_text += f"- Include filter: '{include_filter}'\n"
            if exclude_terms:
                results_text += f"- Exclude terms: {exclude_terms}\n"
            
            # File processing stats
            if stats:
                results_text += f"- Files searched: {stats.get('files_searched', 0)}\n"
                results_text += f"- Files skipped: {stats.get('files_skipped', 0)}\n"
                total_plist_files = stats.get('files_searched', 0) + stats.get('files_skipped', 0)
                if total_plist_files > 0:
                    results_text += f"- Total .plist files found: {total_plist_files}\n"
            
            results_text += "\n"
            
            # Breakdown by search term if multiple
            if len(search_strings) > 1:
                results_text += "Breakdown by search term:\n"
                term_counts = df['Search_String'].value_counts()
                for term, count in term_counts.items():
                    results_text += f"  '{term}': {count} matches\n"
                results_text += "\n"
            
            # Show files that were searched
            unique_files = df['File_Name'].nunique()
            results_text += f"Files with matches: {unique_files} unique files\n"
            if unique_files <= 10:
                file_list = df['File_Name'].unique()
                for file_name in sorted(file_list):
                    results_text += f"  - {file_name}\n"
            else:
                results_text += "  (Too many files to list individually)\n"
            results_text += "\n"
            
            # Detailed results (first 50 to avoid overwhelming the display)
            results_text += "Detailed Results (showing first 50 matches):\n"
            results_text += "-" * 80 + "\n"
            
            display_df = df.head(50)
            for _, row in display_df.iterrows():
                results_text += f"Match {row['Index']}:\n"
                results_text += f"  Search String: {row['Search_String']}\n"
                results_text += f"  PList: {row['PList_Name']}\n"
                results_text += f"  File: {row['File_Name']}\n"
                results_text += f"  Line: {row['Line_Number']}\n"
                results_text += f"  Path: {row['File_Path']}\n\n"
            
            if len(df) > 50:
                results_text += f"... and {len(df) - 50} more matches\n"
            
            self.results_text.insert(tk.END, results_text)
            
            # Save to Excel if requested
            if self.save_excel.get():
                try:
                    self.save_to_excel(df, search_strings, self.output_path.get())
                    self.results_text.insert(tk.END, f"\nResults saved to Excel in: {self.output_path.get()}\n")
                except Exception as e:
                    self.results_text.insert(tk.END, f"\nError saving to Excel: {str(e)}\n")
            
        except Exception as e:
            self.show_error(f"Error displaying results: {str(e)}")
    
    def show_error(self, error_message):
        """Show error message"""
        self.progress.stop()
        self.search_button.config(state='normal')
        self.status_label.config(text="Error occurred")
        messagebox.showerror("Error", error_message)
    
    # Search functions with enhanced file filtering
    def search_string_in_plist_files(self, root_folder, search_strings):
        if isinstance(search_strings, str):
            search_list = [search_strings]
        else:
            search_list = search_strings
        
        result = {
            'Seed': {},
            'File': {},
            'linenumber': {},
            'PList': {}
        }
        
        idx = 0
        files_searched = 0
        files_skipped = 0
        
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file.lower().endswith('.plist'):
                    # Apply file filters (both include and exclude)
                    if not self.should_search_file(file):
                        files_skipped += 1
                        continue
                    
                    files_searched += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        current_plist = "Unknown"
                        
                        for line_number, line in enumerate(lines, 1):
                            plist_match = re.search(r'GlobalPList\s+(\S+)', line)
                            if plist_match:
                                current_plist = plist_match.group(1)
                            
                            for search_string in search_list:
                                if search_string in line:
                                    result['Seed'][idx] = search_string
                                    result['File'][idx] = file_path
                                    result['linenumber'][idx] = line_number
                                    result['PList'][idx] = current_plist
                                    idx += 1
                                
                    except Exception as e:
                        continue
        
        # Store search statistics for display
        result['_stats'] = {
            'files_searched': files_searched,
            'files_skipped': files_skipped
        }
        
        return result
    
    def search_string_in_plist_files_case_insensitive(self, root_folder, search_strings):
        if isinstance(search_strings, str):
            search_list = [search_strings]
        else:
            search_list = search_strings
        
        result = {
            'Seed': {},
            'File': {},
            'linenumber': {},
            'PList': {}
        }
        
        idx = 0
        search_list_lower = [s.lower() for s in search_list]
        files_searched = 0
        files_skipped = 0
        
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file.lower().endswith('.plist'):
                    # Apply file filters
                    if not self.should_search_file(file):
                        files_skipped += 1
                        continue
                    
                    files_searched += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        current_plist = "Unknown"
                        
                        for line_number, line in enumerate(lines, 1):
                            plist_match = re.search(r'GlobalPList\s+(\S+)', line)
                            if plist_match:
                                current_plist = plist_match.group(1)
                            
                            line_lower = line.lower()
                            for i, search_string_lower in enumerate(search_list_lower):
                                if search_string_lower in line_lower:
                                    result['Seed'][idx] = search_list[i]
                                    result['File'][idx] = file_path
                                    result['linenumber'][idx] = line_number
                                    result['PList'][idx] = current_plist
                                    idx += 1
                                
                    except Exception as e:
                        continue
        
        result['_stats'] = {
            'files_searched': files_searched,
            'files_skipped': files_skipped
        }
        
        return result
    
    def search_regex_in_plist_files(self, root_folder, patterns):
        if isinstance(patterns, str):
            pattern_list = [patterns]
        else:
            pattern_list = patterns
        
        result = {
            'Seed': {},
            'File': {},
            'linenumber': {},
            'PList': {}
        }
        
        idx = 0
        files_searched = 0
        files_skipped = 0
        
        try:
            compiled_patterns = [re.compile(pattern) for pattern in pattern_list]
        except re.error as e:
            raise Exception(f"Invalid regular expression: {e}")
        
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                if file.lower().endswith('.plist'):
                    # Apply file filters
                    if not self.should_search_file(file):
                        files_skipped += 1
                        continue
                    
                    files_searched += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        current_plist = "Unknown"
                        
                        for line_number, line in enumerate(lines, 1):
                            plist_match = re.search(r'GlobalPList\s+(\S+)', line)
                            if plist_match:
                                current_plist = plist_match.group(1)
                            
                            for compiled_pattern in compiled_patterns:
                                matches = compiled_pattern.findall(line)
                                for match in matches:
                                    result['Seed'][idx] = match
                                    result['File'][idx] = file_path
                                    result['linenumber'][idx] = line_number
                                    result['PList'][idx] = current_plist
                                    idx += 1
                                
                    except Exception as e:
                        continue
        
        result['_stats'] = {
            'files_searched': files_searched,
            'files_skipped': files_skipped
        }
        
        return result
    
    def results_to_dataframe(self, results):
        if not results['Seed']:
            return pd.DataFrame()
        
        df_data = []
        for i in range(len(results['Seed'])):
            df_data.append({
                'Index': i,
                'Search_String': results['Seed'][i],
                'PList_Name': results['PList'][i],
                'File_Path': results['File'][i],
                'Line_Number': results['linenumber'][i],
                'File_Name': os.path.basename(results['File'][i])
            })
        
        df = pd.DataFrame(df_data)
        return df
    
    def save_to_excel(self, df, search_terms, output_folder):
        if df.empty:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if isinstance(search_terms, str):
            safe_search_term = re.sub(r'[^\w\-_.]', '_', search_terms)
        else:
            safe_search_term = f"multiple_terms_{len(search_terms)}"
        
        # Add filter info to filename
        include_filter = self.file_filter.get().strip()
        exclude_terms = self.get_exclude_terms()
        
        filename_parts = [f"plist_search_{safe_search_term}"]
        
        if include_filter:
            safe_include = re.sub(r'[^\w\-_.]', '_', include_filter)
            filename_parts.append(f"inc_{safe_include}")
        
        if exclude_terms:
            safe_exclude = re.sub(r'[^\w\-_.]', '_', '_'.join(exclude_terms))
            filename_parts.append(f"exc_{safe_exclude}")
        
        filename_parts.append(timestamp)
        filename = "_".join(filename_parts) + ".xlsx"
        
        filepath = os.path.join(output_folder, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Search_Results', index=False)
            
            search_terms_str = str(search_terms) if isinstance(search_terms, str) else ', '.join(search_terms)
            exclude_terms_str = ', '.join(exclude_terms) if exclude_terms else 'None'
            
            summary_data = {
                'Metric': [
                    'Total Matches', 
                    'Unique Files', 
                    'Unique PLists', 
                    'Search Terms', 
                    'Unique Search Strings Found', 
                    'Include Filter Applied',
                    'Exclude Terms Applied'
                ],
                'Value': [
                    len(df),
                    df['File_Path'].nunique(),
                    df['PList_Name'].nunique(),
                    search_terms_str,
                    df['Search_String'].nunique(),
                    include_filter if include_filter else 'None',
                    exclude_terms_str
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            plist_summary = df.groupby('PList_Name').agg({
                'Index': 'count',
                'File_Path': 'nunique',
                'Search_String': 'nunique'
            }).rename(columns={
                'Index': 'Match_Count', 
                'File_Path': 'File_Count',
                'Search_String': 'Unique_Terms_Found'
            }).reset_index()
            plist_summary.to_excel(writer, sheet_name='PList_Summary', index=False)
            
            if isinstance(search_terms, list) and len(search_terms) > 1:
                term_summary = df.groupby('Search_String').agg({
                    'Index': 'count',
                    'File_Path': 'nunique',
                    'PList_Name': 'nunique'
                }).rename(columns={
                    'Index': 'Match_Count',
                    'File_Path': 'File_Count',
                    'PList_Name': 'PList_Count'
                }).reset_index()
                term_summary.to_excel(writer, sheet_name='Term_Summary', index=False)

def main():
    root = tk.Tk()
    app = PListSearchGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()