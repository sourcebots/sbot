import functools
import logging
import sys
from typing import Callable, TypeVar

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec
Param = ParamSpec("Param")
RetType = TypeVar("RetType")

E = TypeVar("E", bound=BaseException)

TRACE = 5


def logger_setup() -> None:
    logging.addLevelName(TRACE, "TRACE")


def log_to_debug(func: Callable[Param, RetType]) -> Callable[Param, RetType]:
    """Print the function signature and return value"""
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def wrapper_debug(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)

        logger.debug(f"Calling {func.__qualname__}({signature})")
        value = func(*args, **kwargs)
        logger.debug(f"{func.__qualname__!r} returned {value!r}")

        return value
    return wrapper_debug
