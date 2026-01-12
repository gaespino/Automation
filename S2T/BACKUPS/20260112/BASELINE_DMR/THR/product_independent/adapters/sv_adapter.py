from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog


class SvAdapter:
    def __init__(self, sv, logger):
        # type: (any, ILog) -> None
        self._sv = sv
        self._base_access = None
        self._logger = logger
        #super(SvAdapter, self).__init__(sv, logger)

    @staticmethod
    def restart_globalbase():
        import svtools.common.baseaccess
        base = svtools.common.baseaccess.getglobalbase(refresh=True)
        base.restart()

    def recover(self):
        import namednodes
        self._sv = None
        self._logger.log("Initializing PythonSV...")
        namednodes.sv.initialize()
        self._logger.log("Refreshing PythonSV...")
        self._sv = namednodes.sv.get_manager(["socket"])
        self.restart_globalbase()
        self._sv.refresh()
        self._logger.log("SV object returned: %s" % str(self._sv))
