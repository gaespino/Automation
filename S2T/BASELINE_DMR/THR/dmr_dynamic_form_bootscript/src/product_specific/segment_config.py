class SegmentConfig:
    """Handles module count per die and valid ranges depending on segment."""

    SUPPORTED_SEGMENTS = {
        'DMRUCC': 32,
        'DMRHCC': 20,
    }

    def __init__(self, segment: str):
        if segment not in self.SUPPORTED_SEGMENTS:
            raise ValueError(f"Unsupported segment: {segment}")
        self.segment = segment
        self.module_count_per_die = self.SUPPORTED_SEGMENTS[segment]

    def get_valid_range(self, cbb_id: int) -> range:
        """
        Returns the valid range of modules for a given cbb_id.
        """
        start = cbb_id * 32
        end = start + self.module_count_per_die
        return range(start, end)
