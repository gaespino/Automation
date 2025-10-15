import traceback

# Exception Handler
def formatException(e):
    """Format exception with line number and function name"""
    tb = traceback.extract_tb(e.__traceback__)[-1]
    return f"{type(e).__name__}: {e} at line {tb.lineno} in {tb.name}()"
