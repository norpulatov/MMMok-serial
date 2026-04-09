import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatMemberStatus
from aiogram.types import CallbackQuery, InlineQuery, Message, TelegramObject

from app.db import crud
from app.db.database import SessionLocal
from app.keyboards.inline import force_sub_check_keyboard


logger = logging.getLogger(__name__)


class ForceSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if data.get("is_admin"):
            return await handler(event, data)

        # Do not block internal check callback itself.
        if isinstance(event, CallbackQuery) and event.data == "sub:check":
            return await handler(event, data)

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        async with SessionLocal() as session:
            settings = await crud.get_or_create_bot_settings(session)

        if not settings.force_sub_enabled or not settings.force_sub_channel_id:
            return await handler(event, data)

        try:
            member = await data["bot"].get_chat_member(settings.force_sub_channel_id, user.id)
            is_member = member.status in {
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
            }
        except Exception:
            logger.exception("A'zolik tekshiruvida xatolik")
            # Fallback: do not block if API check fails unexpectedly.
            return await handler(event, data)

        if is_member:
            return await handler(event, data)

        text = "Botdan to'liq foydalanish uchun avval kanalga a'zo bo'ling."
        keyboard = force_sub_check_keyboard(settings.force_sub_channel_link)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
            return None
        if isinstance(event, CallbackQuery):
            await event.message.answer(text, reply_markup=keyboard)
            await event.answer("Avval kanalga a'zo bo'ling.", show_alert=True)
            return None
        if isinstance(event, InlineQuery):
            await event.answer([], is_personal=True, cache_time=1, switch_pm_text="Avval kanalga a'zo bo'ling", switch_pm_parameter="start")
            return None

        return await handler(event, data)
