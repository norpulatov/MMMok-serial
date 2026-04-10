import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject

from app.config import get_settings
from app.db.database import SessionLocal, init_db
from app.handlers import all_routers
from app.middlewares.auth import AdminMiddleware
from app.middlewares.subscription import ForceSubscriptionMiddleware


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with SessionLocal() as session:
            data['session'] = session
            return await handler(event, data)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    settings = get_settings()
    await init_db()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    dp.inline_query.middleware(AdminMiddleware())
    dp.message.middleware(ForceSubscriptionMiddleware())
    dp.callback_query.middleware(ForceSubscriptionMiddleware())
    dp.inline_query.middleware(ForceSubscriptionMiddleware())

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.inline_query.middleware(DbSessionMiddleware())

    for router in all_routers:
        dp.include_router(router)

    logging.info('Bot ishga tushdi.')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
