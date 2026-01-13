from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from .config import load_settings
from .db import Database
from .i18n import normalize_lang


async def main() -> None:
    settings = load_settings()
    if not settings.support_bot_token:
        raise RuntimeError("Missing SUPPORT_BOT_TOKEN")

    db = Database(settings.db_path)
    await db.init()

    bot = Bot(token=settings.support_bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(m: Message) -> None:
        user = await db.upsert_user(m.from_user.id, m.from_user.first_name, m.from_user.username)
        lang = normalize_lang(user.language)
        _ = lang  # reserved
        text = (
            "👋 <b>Welcome to Support!</b>\n\n"
            f"🆔 ID: <code>{m.from_user.id}</code>\n"
            "How can I help you?\n\n"
            "Send your message here and it will be forwarded to admin."
        )
        await m.answer(text)

    @dp.message(F.reply_to_message)
    async def admin_reply(m: Message) -> None:
        # only admin replies are processed
        if m.from_user.id != settings.admin_id:
            return
        if not m.reply_to_message:
            return
        admin_msg_id = m.reply_to_message.message_id
        uid = await db.support_map_get_user(admin_msg_id)
        if not uid:
            return
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=m.chat.id, message_id=m.message_id)
        except Exception:
            await m.answer("❌ Failed to send to user.")

    @dp.message()
    async def user_message(m: Message) -> None:
        if m.from_user.id == settings.admin_id:
            return
        try:
            sent = await bot.copy_message(chat_id=settings.admin_id, from_chat_id=m.chat.id, message_id=m.message_id)
            await db.support_map_add(admin_message_id=sent.message_id, user_id=m.from_user.id)
            await m.answer("✅ Sent to support. Please wait for admin reply.")
        except Exception:
            await m.answer("❌ Failed to send. Try again later.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
