import functools
from src.config.logging_conf import get_logger
from aiogram.types import CallbackQuery, Message
from typing import Any, Callable, Awaitable


def log_router_call(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """
    Decorator to log when a router handler is called and when it finishes.
    Logs handler name, user/callback/message info, and exceptions.
    """
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Try to extract CallbackQuery or Message from args
        cbq = None
        msg = None
        for arg in args:
            if isinstance(arg, CallbackQuery):
                cbq = arg
            elif isinstance(arg, Message):
                msg = arg
        handler_name = func.__name__
        user_id = None
        if cbq and cbq.from_user:
            user_id = cbq.from_user.id
        elif msg and msg.from_user:
            user_id = msg.from_user.id
        logger.info(f"[Router] Handler '{handler_name}' called by user_id={user_id}")
        try:
            result = await func(*args, **kwargs)
            logger.info(
                f"[Router] Handler '{handler_name}' finished for user_id={user_id}"
            )
            return result
        except Exception as e:
            logger.exception(
                f"[Router] Handler '{handler_name}' error for user_id={user_id}: {e}"
            )
            raise

    return wrapper
