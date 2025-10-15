from diamondrapids.users.THR.product_independent.interfaces.ilog import ILog
from typing import List


class MaskManipulator:
    """Encapsulates logic for modifying the mask bits."""

    def __init__(self, logger: ILog, enable: bool):
        self.logger = logger
        self.enable = enable

    def apply_changes(self, relative_bits: List[int], current_mask: int) -> int:
        new_mask = current_mask

        for bit_item in relative_bits:
            # Calculate relative bit index for this cbb_id
            mask_bit = 1 << bit_item
            bit_is_set = bool(new_mask & mask_bit)
            if self.enable:  # Turn ON
                if bit_is_set:
                    self.logger.log(f"WARNING: Bit {bit_item} is already ON")
                new_mask |= mask_bit
            else:  # Turn OFF
                if not bit_is_set:
                    self.logger.log(f"WARNING: Bit {bit_item} is already OFF"
                    )
                new_mask &= ~mask_bit
        return new_mask