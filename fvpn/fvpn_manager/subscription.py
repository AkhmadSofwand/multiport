\
from __future__ import annotations

from typing import List, Tuple

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest


async def check_user_subscriptions(bot: Bot, user_id: int, required_channels: List[str]) -> Tuple[bool, List[str]]:
    """
    Returns (ok, missing_channels)
    Note: Bot must be present in those channels (preferably as admin) to check membership reliably.
    """
    missing: List[str] = []
    for ch in required_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            # status can be: creator, administrator, member, restricted, left, kicked
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except TelegramBadRequest:
            # if bot cannot access the channel / invalid
            missing.append(ch)
        except Exception:
            missing.append(ch)
    return (len(missing) == 0, missing)
