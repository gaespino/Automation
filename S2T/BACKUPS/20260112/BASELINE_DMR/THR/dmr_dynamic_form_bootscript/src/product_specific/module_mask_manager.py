from diamondrapids.users.THR.dmr_dynamic_form_bootscript.src.product_specific.mask_manipulator import MaskManipulator
from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from typing import List


class ModuleMaskManager:
    """
    High-level class responsible for:
    - Validating module ranges based on cbb_id and segment
    - Delegating mask changes to MaskManipulator
    """

    def __init__(self, logger: ILog, relative_bits: List[int], current_mask: int, enable: bool = True):
        self.logger = logger
        self.relative_bits = relative_bits
        self.current_mask = current_mask
        self.enable = enable
        self.mask_manipulator = MaskManipulator(logger, enable)

    def apply(self) -> int:
        return self.mask_manipulator.apply_changes(
            self.relative_bits, self.current_mask
        )