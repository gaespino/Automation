# Create a new file: framework_utils.py
from users.gaespino.dev.DebugFramework.ExecutionHandler.utils.ThreadsHandler import execution_state, ExecutionCommand
from typing import Optional, Callable

class FrameworkUtils:
    """Utility class for framework integration across modules"""
    
    @staticmethod
    def check_cancellation(context: str = ""):
        """
        Check for cancellation with optional context
        
        Args:
            context: Optional context string for logging
        """
        try:
            if execution_state.is_cancelled():
                msg = f"FWorkUtils: Execution interrupted by user"
                if context:
                    msg += f" in {context}"
                print(msg)
                execution_state.acknowledge_command(ExecutionCommand.CANCEL, f"FWorkUtils: Cancel processed in {context}")
                raise InterruptedError('Execution Interrupted by User')
                
            if execution_state.has_command(ExecutionCommand.EMERGENCY_STOP):
                msg = f"Emergency stop requested"
                if context:
                    msg += f" in {context}"
                print(msg)
                execution_state.acknowledge_command(ExecutionCommand.EMERGENCY_STOP, f"FWorkUtils: Emergency stop processed in {context}")
                raise InterruptedError('Emergency Stop Requested')
                
        except InterruptedError:
            raise
        except Exception as e:
            print(f"FWorkUtils: Error checking cancellation: {e}")
    
    @staticmethod
    def clear_cancellation(logger: Optional[Callable] = None, context: str = ""):
        """Clear cancellation state"""
        try:
            cancel_commands = [ExecutionCommand.CANCEL, ExecutionCommand.EMERGENCY_STOP]
            
            cleared_any = False
            for cmd in cancel_commands:
                if execution_state.has_command(cmd):
                    execution_state.acknowledge_command(cmd, f"FWorkUtils: Cancel cleared in {context}")
                    cleared_any = True
            
            msg = "FWorkUtils: Cancel commands cleared" if cleared_any else "No cancel commands to clear"
            if context:
                msg += f" in {context}"
            
            if logger:
                logger(msg)
            else:
                print(msg)
                
        except Exception as e:
            error_msg = f"FWorkUtils: Error clearing cancellation: {e}"
            if logger:
                logger(error_msg)
            else:
                print(error_msg)
    
    @staticmethod
    def is_execution_active() -> bool:
        """Check if execution is active"""
        try:
            return execution_state.get_state('execution_active', False)
        except Exception:
            return False
    
    @staticmethod
    def is_paused() -> bool:
        """Check if execution is paused"""
        try:
            return execution_state.is_paused()
        except Exception:
            return False
    
    @staticmethod
    def should_stop() -> bool:
        """Check if execution should stop"""
        try:
            return execution_state.should_stop()
        except Exception:
            return False
    
    @staticmethod
    def get_execution_info() -> dict:
        """Get current execution information"""
        try:
            return {
                'active': execution_state.get_state('execution_active', False),
                'current_experiment': execution_state.get_state('current_experiment'),
                'current_iteration': execution_state.get_state('current_iteration', 0),
                'total_iterations': execution_state.get_state('total_iterations', 0),
                'step_mode': execution_state.is_step_mode_enabled(),
                'paused': execution_state.is_paused(),
                'cancelled': execution_state.is_cancelled(),
                'ended': execution_state.is_ended()
            }
        except Exception as e:
            print(f"Error getting execution info: {e}")
            return {}

# Convenience functions for backward compatibility
def check_user_cancel(context: str = ""):
    """Convenience function for cancellation checking"""
    FrameworkUtils.check_cancellation(context)

def clear_cancel_flag(logger: Optional[Callable] = None, context: str = ""):
    """Convenience function for clearing cancellation"""
    FrameworkUtils.clear_cancellation(logger, context)

def is_framework_active() -> bool:
    """Check if framework is active"""
    return FrameworkUtils.is_execution_active()