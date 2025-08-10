import logging
from functools import wraps
from typing import Callable, Awaitable
from telegram.ext import ConversationHandler, Application
from telegram import InlineKeyboardMarkup

from src.error_codes import get_user_message
from src.correlation import get_correlation_id, new_correlation_id

logger = logging.getLogger(__name__)


async def safe_reply(update, text: str, reply_markup=None):
    try:
        if getattr(update, 'callback_query', None):
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error("[cid=%s] Telegram send/edit failed: %s", get_correlation_id(), e)


def guarded_handler(error_code: str) -> Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]:
    """Decorator to wrap async handlers and ensure consistent failure behavior."""
    def decorator(func: Callable[..., Awaitable]):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            # Ensure a correlation id exists for this update
            new_correlation_id()
            try:
                return await func(update, context, *args, **kwargs)
            except Exception as e:
                cid = get_correlation_id()
                user_id = getattr(getattr(update, 'effective_user', None), 'id', 'unknown')
                logger.error("[cid=%s] Handler %s failed for user %s: %s", cid, func.__name__, user_id, e, exc_info=True)
                # Clear any pending state for safety
                try:
                    context.user_data.clear()
                except Exception:
                    pass
                # Send a friendly message
                await safe_reply(update, get_user_message(error_code))
                return ConversationHandler.END
        return wrapper
    return decorator


async def _global_error_handler(update, context):
    cid = get_correlation_id()
    try:
        user_id = getattr(getattr(update, 'effective_user', None), 'id', 'unknown') if update else 'unknown'
        logger.error("[cid=%s] Global error for user %s: %s", cid, user_id, context.error, exc_info=True)
    except Exception:
        logger.error("[cid=%s] Global error (no update): %s", cid, context.error, exc_info=True)
    # Best-effort notify the user if we can
    if update:
        await safe_reply(update, get_user_message("E_UNKNOWN"))


def add_global_error_handler(app: Application) -> None:
    app.add_error_handler(_global_error_handler) 