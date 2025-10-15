import os
import time
from datetime import datetime
import pytz

# Folder configurations
script_dir = os.path.dirname(os.path.abspath(__file__))
base_folder = 'C:\\SystemDebug'
ttl_source = os.path.join(script_dir, 'TTL')
shmoos_source = os.path.join(script_dir, 'Shmoos')
ttl_dest = os.path.join(base_folder, 'TTL')
shmoos_dest = os.path.join(base_folder, 'Shmoos')
logs_dest = os.path.join(base_folder, 'Logs')

PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"

ULX_CPU_DICT = {'GNR': 'GNR_B0', 'CWF': 'CWF -gsv'}

def xformat(e):
    """Format exception for logging"""
    # Import here to avoid circular dependencies
    import users.gaespino.dev.S2T.Tools.utils as s2tutils
    return s2tutils.formatException(e)

def macros_path(ttl_path):
    """Get macro commands dictionary"""
    macrospath = rf'{ttl_path}'
    macro_cmds = {
        'Disconnect': rf'{macrospath}\disconnect.ttl',
        'Connect': rf'{macrospath}\connect.ttl',
        'StartCapture': rf'{macrospath}\Boot.ttl',
        'StartTest': rf'{macrospath}\Commands.ttl',
        'StopCapture': rf'{macrospath}\stop_capture.ttl'
    }
    return macro_cmds

# Default Macros Path
macro_cmds = macros_path(ttl_dest)

def print_separator_box(direction='down'):
    """Print separator box"""
    arrow = 'v' if direction == 'down' else '+'
    separator_line = f'{"-"*50}{arrow}{"-"*50}'
    return separator_line

def print_custom_separator(text):
    """Print custom separator with text"""
    total_length = 101
    text_length = len(text)
    side_length = (total_length - text_length) // 2
    separator_line = f'{"*" * side_length} {text} {"*" * side_length}'
    
    # Adjust if the total length is not exactly 101 due to integer division
    if len(separator_line) < total_length:
        separator_line += '*'
    
    return separator_line

def initscript():
    """Initialize script folders"""
    # Import here to avoid circular dependencies
    import users.gaespino.dev.DebugFramework.FileHandler as fh
    
    # Create base folder if it does not exist
    fh.create_folder_if_not_exists(base_folder)

    # Create TTL and Shmoos folders if they do not exist
    ttlf = fh.create_folder_if_not_exists(ttl_dest)
    shmf = fh.create_folder_if_not_exists(shmoos_dest)
    logsf = fh.create_folder_if_not_exists(logs_dest)

    if not ttlf: 
        replace_files(ttl=True, shmoo=False, replace=True)
    if not shmf: 
        replace_files(ttl=False, shmoo=True, replace=True)

    print('Operation completed.')

def replace_files(ttl, shmoo, replace=False):
    """Replace TTL and shmoo files"""
    # Import here to avoid circular dependencies
    import users.gaespino.dev.DebugFramework.FileHandler as fh
    
    if replace: 
        user_input = "Y"
    else: 
        user_input = ""
    
    # Copy files to TTL and Shmoos folders
    if ttl:
        fh.copy_files(ttl_source, ttl_dest, uinput=user_input)
    if shmoo:
        fh.copy_files(shmoos_source, shmoos_dest, uinput=user_input)

def currentTime():
    """Get current time in GMT-6"""
    # Define the GMT-6 timezone
    gmt_minus_6 = pytz.timezone('Etc/GMT+6')

    # Get the current time in GMT-6
    current_time_gmt_minus_6 = datetime.now(gmt_minus_6)

    # Print the current time in GMT-6
    print("Current time in GMT-6:", current_time_gmt_minus_6.strftime('%Y-%m-%d %H:%M:%S'))

    return current_time_gmt_minus_6