from typing import NamedTuple


class BoardIdentity(NamedTuple):
    manufacturer: str
    board_type: str
    asset_tag: str
    sw_version: str


def map_to_int(x, in_min, in_max, out_min, out_max):
    if (x < in_min) or (x > in_max):
        raise ValueError(f'Value provided outside range, provided:{x}, min:{in_min}, max:{in_max}')
    value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(value)


def map_to_float(x, in_min, in_max, out_min, out_max, precision=3):
    value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return round(value, precision)
