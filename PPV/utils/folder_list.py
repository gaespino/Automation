import os

def list_files_in_directory(directory):
    # Check if the directory exists
    if not os.path.isdir(directory):
        print(f"Directory {directory} does not exist.")
        return []

    # List all files in the directory
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def save_list_to_file(file_list, output_file):
    with open(output_file, 'w') as f:
        for file in file_list:
            f.write(f"{file}\n")

if __name__ == "__main__":
    # Specify the directory to list files from
    directory_to_list = r"I:\intel\engineering\dev\user_links\gaespino\GNR\Pats\DragonNewRegression\pat\indv_bin"

    # Specify the output file path
    output_file_path = r"C:\Temp\file_list.txt"

    # List files in the specified directory
    file_list = list_files_in_directory(directory_to_list)

    # Save the list to the output file
    save_list_to_file(file_list, output_file_path)

    print(f"List of files saved to {output_file_path}")