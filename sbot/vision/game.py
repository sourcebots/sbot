"""Game specific code."""


def get_marker_size(marker_id: int) -> int:
    """
    Get the size of a marker in millimetres.

    :param marker_id: An official marker number, mapped to the competitor range.
    :returns: Size of the marker in millimetres.
    """
    if marker_id in range(0, 100):
        return 80
    else:
        return 200
