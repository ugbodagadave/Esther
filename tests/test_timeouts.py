import unittest
from unittest.mock import AsyncMock, MagicMock
from telegram.ext import Application, ContextTypes
from telegram import Update, User

from src.main import schedule_state_timeout, timeout_job, cancel_any_flow


class TestTimeouts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app = Application.builder().token("test-token").build()

    async def _mk_update_context(self):
        user = User(id=123, first_name="Test", is_bot=False, username="testuser")
        update = MagicMock(spec=Update)
        update.effective_user = user
        update.effective_chat = MagicMock()
        update.effective_chat.id = 999
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        context = ContextTypes.DEFAULT_TYPE(application=self.app, chat_id=999, user_id=123)

        return update, context

    async def test_schedule_state_timeout(self):
        update, context = await self._mk_update_context()
        schedule_state_timeout(update, context, "AWAIT_CONFIRMATION")
        jobs = context.job_queue.get_jobs_by_name("timeout:999:AWAIT_CONFIRMATION")
        self.assertTrue(len(jobs) >= 1)

    async def test_timeout_job_sends_message(self):
        # Create a fake job context
        class Job:
            def __init__(self):
                self.chat_id = 999
                self.data = {"state": "AWAIT_CONFIRMATION"}
        ctx = MagicMock()
        ctx.job = Job()
        ctx.bot = MagicMock()
        ctx.bot.send_message = AsyncMock()
        await timeout_job(ctx)
        ctx.bot.send_message.assert_awaited()

    async def test_cancel_any_flow(self):
        update, context = await self._mk_update_context()
        result = await cancel_any_flow(update, context)
        self.assertEqual(result, -1)  # ConversationHandler.END 