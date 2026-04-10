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

        channels = await crud.list_force_sub_channels(session)
        channel_links = [item.channel_link for item in channels if item.channel_link]
        if not settings.force_sub_enabled or not channels:
            return await handler(event, data)

        try:
            is_member = True
            for channel in channels:
                member = await data["bot"].get_chat_member(channel.channel_id, user.id)
                joined = member.status in {
                    ChatMemberStatus.MEMBER,
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.CREATOR,
                }
                if not joined:
                    is_member = False
                    break
        except Exception:
            logger.exception("A'zolik tekshiruvida xatolik")
            text = (
                "⚠️ A'zolik tekshiruvini bajara olmadim.\n"
                "Kanal ID yoki botning kanal huquqlarini tekshiring."
            )
            keyboard = force_sub_check_keyboard(channel_links)
            if isinstance(event, Message):
                await event.answer(text, reply_markup=keyboard)
                return None
            if isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=keyboard)
                await event.answer("A'zolik tekshiruvi ishlamadi.", show_alert=True)
                return None
            if isinstance(event, InlineQuery):
                await event.answer(
                    [],
                    is_personal=True,
                    cache_time=1,
                    switch_pm_text="A'zolik tekshiruvi ishlamadi",
                    switch_pm_parameter="start",
                )
                return None
            return None

        if is_member:
            return await handler(event, data)

        text = "Botdan to'liq foydalanish uchun avval kanalga a'zo bo'ling."
        keyboard = force_sub_check_keyboard(channel_links)

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
