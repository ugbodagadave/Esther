import logging
from functools import wraps
from typing import Callable, Awaitable, List, Optional
from telegram.ext import ConversationHandler, Application
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from src.error_codes import get_user_message
from src.correlation import get_correlation_id, new_correlation_id
from src.failure_advisor import FailureAdvisor

logger = logging.getLogger(__name__)

# Singleton advisor (lazy usable via enabled flag)
failure_advisor = FailureAdvisor()


async def safe_reply(update, text: str, reply_markup=None, actions: Optional[List[str]] = None):
    try:
        # Build dynamic action buttons if provided
        if actions:
            keyboard = [[InlineKeyboardButton(a, callback_data=f"action:{a.lower()}")] for a in actions]
            reply_markup = InlineKeyboardMarkup(keyboard)
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

                # Build structured error context for advisor
                try:
                    user_message = None
                    if getattr(update, 'message', None) and getattr(update.message, 'text', None):
                        user_message = update.message.text
                    elif getattr(update, 'callback_query', None) and getattr(update.callback_query, 'data', None):
                        user_message = update.callback_query.data

                    intent = None
                    entities = None
                    if isinstance(getattr(context, 'user_data', {}), dict):
                        intent = context.user_data.get('intent')
                        entities = context.user_data.get('entities')
                        circuit_state = context.user_data.get('last_circuit')
                    else:
                        circuit_state = None

                    # Attempt to introspect circuit info from exception if present
                    if not circuit_state:
                        circuit_state = getattr(e, 'circuit', None)

                    error_context = {
                        "correlation_id": cid,
                        "handler": func.__name__,
                        "error_code": error_code,
                        "user_message": user_message,
                        "intent": intent,
                        "entities": entities,
                        "circuit_state": circuit_state,
                    }
                except Exception:
                    error_context = {"error_code": error_code}

                advisor_message = None
                advisor_actions = None
                try:
                    if failure_advisor.enabled:
                        advice = failure_advisor.summarize(error_context)
                        if advice and isinstance(advice, dict):
                            advisor_message = advice.get("message")
                            advisor_actions = advice.get("actions")
                except Exception:
                    # Never allow advisor issues to affect user flow
                    advisor_message = None
                    advisor_actions = None

                # Compose final user message
                final_message = advisor_message or get_user_message(error_code)

                # Send a friendly message with optional actions
                await safe_reply(update, final_message, actions=advisor_actions)
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