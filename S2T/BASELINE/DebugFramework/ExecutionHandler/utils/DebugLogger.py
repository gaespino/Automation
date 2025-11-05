import sys
import threading
from datetime import datetime
from typing import Optional, TextIO

class DebugLogger:
    """Simple debug logger for framework and external scripts"""
    
    def __init__(self, name: str = "DebugLogger", enabled: bool = False,  # Changed default to False
                 output_file: Optional[str] = None, console_output: bool = True):
        self.name = name
        self.enabled = enabled  # Now defaults to False
        self.console_output = console_output
        self.output_file = output_file
        self._lock = threading.Lock()
        self._file_handle: Optional[TextIO] = None
        
        # Only open file if enabled
        if self.enabled and self.output_file:
            try:
                self._file_handle = open(self.output_file, 'a', encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not open debug log file {self.output_file}: {e}")
                self._file_handle = None
    
    def debug_log(self, message: str, level: int = 1, category: str = "DEBUG"):
        """
        Log debug message
        
        Args:
            message: Message to log
            level: Debug level (1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL)
            category: Message category for filtering
        """
        if not self.enabled:
            return  # Early return if disabled
            
        level_names = {1: "INFO", 2: "WARN", 3: "ERROR", 4: "CRITICAL"}
        level_name = level_names.get(level, "DEBUG")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        thread_name = threading.current_thread().name
        
        formatted_message = f"[{timestamp}] [{self.name}] [{level_name}] [{category}] [{thread_name}] {message}"
        
        with self._lock:
            if self.console_output:
                print(formatted_message)
            
            if self._file_handle:
                try:
                    self._file_handle.write(formatted_message + '\n')
                    self._file_handle.flush()
                except Exception as e:
                    print(f"Error writing to debug log file: {e}")
    
    def enable(self, output_file: Optional[str] = None):
        """Enable debug logging"""
        with self._lock:
            self.enabled = True
            
            # Set up file output if provided
            if output_file:
                self.output_file = output_file
                if self._file_handle:
                    try:
                        self._file_handle.close()
                    except Exception:
                        pass
                
                try:
                    self._file_handle = open(self.output_file, 'a', encoding='utf-8')
                except Exception as e:
                    print(f"Warning: Could not open debug log file {self.output_file}: {e}")
                    self._file_handle = None
    
    def disable(self):
        """Disable debug logging"""
        with self._lock:
            self.enabled = False
            # Keep file handle open in case we re-enable
    
    def close(self):
        """Close file handle if open"""
        with self._lock:
            if self._file_handle:
                try:
                    self._file_handle.close()
                except Exception:
                    pass
                finally:
                    self._file_handle = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close()

# Global debug logger instance for easy access - DISABLED BY DEFAULT
_global_debug_logger = DebugLogger("Framework", enabled=False)  # Changed to False

def debug_log(message: str, level: int = 1, category: str = "DEBUG"):
    """Global debug logging function"""
    _global_debug_logger.debug_log(message, level, category)

def set_global_debug_enabled(enabled: bool, log_file: Optional[str] = None):
    """Enable/disable global debug logging"""
    if enabled:
        _global_debug_logger.enable(log_file)
    else:
        _global_debug_logger.disable()

def set_global_debug_file(file_path: str):
    """Set global debug log file"""
    _global_debug_logger.close()
    _global_debug_logger.output_file = file_path
    if _global_debug_logger.enabled and file_path:
        try:
            _global_debug_logger._file_handle = open(file_path, 'a', encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not open debug log file {file_path}: {e}")

def is_debug_enabled() -> bool:
    """Check if debug logging is enabled"""
    return _global_debug_logger.enabled