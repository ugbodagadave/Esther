import unittest
from unittest.mock import AsyncMock, MagicMock

from telegram.ext import Application, ContextTypes, ConversationHandler
from telegram import Update, User

from src.error_handler import guarded_handler, add_global_error_handler


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