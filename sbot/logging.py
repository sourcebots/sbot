import logging

TRACE_LEVEL_NUM = 5


def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        # Logger takes its '*args' as 'args'.
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


def logger_setup() -> None:
    logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
    logging.Logger.trace = trace
    logging.TRACE = TRACE_LEVEL_NUM
