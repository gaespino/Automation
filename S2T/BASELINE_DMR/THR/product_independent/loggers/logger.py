from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog

class Logger(ILog):
    def log(self, msg): print(f"[INFO] {msg}")
