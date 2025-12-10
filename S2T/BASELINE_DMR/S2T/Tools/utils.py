import traceback
import py2ipc
import ipccli

ipc = ipccli.baseaccess()

# Exception Handler
def formatException(e):
    """Format exception with line number and function name"""
    tb = traceback.extract_tb(e.__traceback__)[-1]
    return f"{type(e).__name__}: {e} at line {tb.lineno} in {tb.name}()"


# IPC operations    

def entercredentials(username, password):
        """

        Used to save credentials so that future calls to unlock
        will not prompt the user for their username and password.

        Args:
            device (int): Not needed or used, only exists to maintain consistency


        The unlock command will also set credentials, but
        only if the unlock command completes successfully.
        Use clearcredentials to clear the data stored by this function.

        See Also:
            - :py:meth:`~ipccli.ipc_env.ipc_commands.Commands.clearcredentials`
            - :py:meth:`~ipccli.ipc_env.ipc_commands.Commands.requirescredentials`
            - :py:meth:`~ipccli.ipc_env.ipc_commands.Commands.unlock`

        **IPC services required:** Authorization

        """
        authzservice = py2ipc.IPC_GetService("Authorization")
        authzservice.SetCredentials(username, password)

def clearcredentials():
    """
    Clear any stored credentials previously set
    by entercredentials or unlock.
    """
    ipc.clearcredentials()

def isauthorized():
    """
    Check if IPC is authorized

    Returns:
        bool: True if authorized, False otherwise
    """
    
    return ipc.isauthorized()

def ipc_unlock():
    """
    Unlock IPC session
    """
    ipc.unlock()

def ipc_lock():
    """
    Lock IPC session
    """
    ipc.lock()
