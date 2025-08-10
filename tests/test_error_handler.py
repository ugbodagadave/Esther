import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram.ext import Application, ContextTypes, ConversationHandler
from telegram import Update, User

from src.error_handler import guarded_handler, add_global_error_handler, failure_advisor


class TestErrorHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = Application.builder().token("test-token").build()

    async def _mk_update_context(self):
        user = User(id=123, first_name="Test", is_bot=False, username="testuser")
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        update.effective_user = user
        context = ContextTypes.DEFAULT_TYPE(application=self.app, chat_id=123, user_id=123)
        # Seed user_data as a dict-like (it is in real app)
        context.user_data.clear()
        return update, context

    async def test_guarded_handler_converts_exception(self):
        @guarded_handler("E_UNKNOWN")
        async def boom(update, context):
            raise RuntimeError("boom")

        update, context = await self._mk_update_context()
        res = await boom(update, context)
        self.assertEqual(res, ConversationHandler.END)
        update.message.reply_text.assert_awaited()

    async def test_global_error_handler(self):
        # Register and invoke global error handler path by raising from handler
        @guarded_handler("E_UNKNOWN")
        async def ok(update, context):
            return ConversationHandler.END

        add_global_error_handler(self.app)
        update, context = await self._mk_update_context()
        # Simulate calling ok (should not trigger global), just ensure it runs
        res = await ok(update, context)
        self.assertEqual(res, ConversationHandler.END)

    async def test_guarded_handler_calls_failure_advisor(self):
        # Mock advisor to return structured advice
        with patch.dict('os.environ', {'ERROR_ADVISOR_ENABLED': 'true'}), \
             patch.object(failure_advisor, 'summarize', return_value={"message": "Try again shortly.", "actions": ["Retry", "Help"]}):

            @guarded_handler("E_OKX_HTTP")
            async def boom(update, context):
                # Make some context for advisor
                context.user_data["intent"] = "get_price"
                context.user_data["entities"] = {"symbol": "ETH"}
                raise RuntimeError("api down")

            update, context = await self._mk_update_context()
            res = await boom(update, context)
            self.assertEqual(res, ConversationHandler.END)
            # Should use edit_message_text or reply_text with keyboard; we verify reply_text got called with text
            update.message.reply_text.assert_awaited()
            args, kwargs = update.message.reply_text.call_args
            self.assertIn("Try again shortly.", args[0])

    async def test_safe_reply_renders_actions(self):
        with patch.dict('os.environ', {'ERROR_ADVISOR_ENABLED': 'true'}), \
             patch.object(failure_advisor, 'summarize', return_value={"message": "Oops.", "actions": ["Retry", "Help", "Wait"]}):

            @guarded_handler("E_UNKNOWN")
            async def boom(update, context):
                raise RuntimeError("oops")

            update, context = await self._mk_update_context()
            res = await boom(update, context)
            self.assertEqual(res, ConversationHandler.END)
            # Ensure called once
            update.message.reply_text.assert_awaited()
            # reply_markup should be present in kwargs
            _, kwargs = update.message.reply_text.call_args
            self.assertIn('reply_markup', kwargs)
            self.assertIsNotNone(kwargs['reply_markup'])

    async def test_fallback_when_advisor_fails(self):
        # Advisor returns None -> use static message
        with patch.dict('os.environ', {'ERROR_ADVISOR_ENABLED': 'true'}), \
             patch.object(failure_advisor, 'summarize', return_value=None):

            @guarded_handler("E_UNKNOWN")
            async def boom(update, context):
                raise RuntimeError("oops")

            update, context = await self._mk_update_context()
            res = await boom(update, context)
            self.assertEqual(res, ConversationHandler.END)
            update.message.reply_text.assert_awaited()
            args, _ = update.message.reply_text.call_args
            # Static message includes generic unexpected error text
            self.assertIn("unexpected error", args[0].lower()) 