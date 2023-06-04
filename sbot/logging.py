import logging

TRACE = 5


def logger_setup() -> None:
    logging.addLevelName(TRACE, "TRACE")
