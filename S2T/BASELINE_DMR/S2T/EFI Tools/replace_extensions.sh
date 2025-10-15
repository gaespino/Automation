#!/bin/bash

# Script to replace file extensions in a directory
# Usage: ./replace_extensions.sh <path> <original_extension> <new_extension>

# Function to display usage
show_usage() {
    echo "Usage: $0 <path> <original_extension> <new_extension>"
    echo ""
    echo "Parameters:"
    echo "  path              - Directory path to search for files"
    echo "  original_extension - Current file extension (without dot, e.g., 'txt')"
    echo "  new_extension     - New file extension (without dot, e.g., 'bak')"
    echo ""
    echo "Examples:"
    echo "  $0 /home/user/documents txt bak"
    echo "  $0 . jpg png"
    echo "  $0 /path/to/files log old"
}

# Check if correct number of arguments provided
if [ $# -ne 3 ]; then
    echo "Error: Invalid number of arguments"
    show_usage
    exit 1
fi

# Assign variables
path="$1"
orig_ext="$2"
new_ext="$3"

# Validate path exists
if [ ! -d "$path" ]; then
    echo "Error: Directory '$path' does not exist"
    exit 1
fi

# Remove leading dots from extensions if present
orig_ext="${orig_ext#.}"
new_ext="${new_ext#.}"

# Validate extensions are not empty
if [ -z "$orig_ext" ] || [ -z "$new_ext" ]; then
    echo "Error: Extensions cannot be empty"
    exit 1
fi

echo "Starting file extension replacement..."
echo "Directory: $path"
echo "Original extension: .$orig_ext"
echo "New extension: .$new_ext"
echo ""

# Counter for renamed files
count=0

# Find and rename files
for file in "$path"/*."$orig_ext"; do
    # Check if file exists (handles case where no files match the pattern)
    if [ -f "$file" ]; then
        # Get the base name without extension
        basename="${file%.*}"
        new_filename="${basename}.${new_ext}"
        
        # Check if target file already exists
        if [ -e "$new_filename" ]; then
            echo "Warning: Target file '$new_filename' already exists. Skipping '$file'"
            continue
        fi
        
        # Rename the file
        if mv "$file" "$new_filename"; then
            echo "Renamed: $(basename "$file") -> $(basename "$new_filename")"
            ((count++))
        else
            echo "Error: Failed to rename '$file'"
        fi
    fi
done

# Handle case where no files were found
if [ $count -eq 0 ]; then
    echo "No files with extension '.$orig_ext' found in '$path'"
else
    echo ""
    echo "Successfully renamed $count file(s)"
fi

echo "Operation completed."