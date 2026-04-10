from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BotSettings, ForceSubChannel, Movie, MoviePart, User


async def create_or_update_user(
    session: AsyncSession, user_id: int, username: str | None, first_name: str
) -> User:
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            added_at=datetime.utcnow(),
        )
        session.add(user)
    else:
        user.username = username
        user.first_name = first_name
    await session.commit()
    return user


async def get_next_movie_number(session: AsyncSession) -> int:
    result = await session.execute(select(func.max(Movie.movie_number)))
    return (result.scalar() or 0) + 1


async def create_movie(
    session: AsyncSession,
    *,
    title: str,
    description: str | None,
    file_id: str,
    preview_file_id: str | None,
    channel_message_id: int | None,
    channel_chat_id: int | None,
    added_by: int,
) -> Movie:
    movie = Movie(
        movie_number=await get_next_movie_number(session),
        title=title,
        description=description,
        file_id=file_id,
        preview_file_id=preview_file_id,
        channel_message_id=channel_message_id,
        channel_chat_id=channel_chat_id,
        added_by=added_by,
    )
    session.add(movie)
    await session.commit()
    await session.refresh(movie)
    return movie


async def get_movie_by_number(session: AsyncSession, movie_number: int) -> Movie | None:
    result = await session.execute(select(Movie).where(Movie.movie_number == movie_number))
    return result.scalar_one_or_none()


async def list_movies(session: AsyncSession, page: int = 1, per_page: int = 10) -> list[Movie]:
    offset = (page - 1) * per_page
    result = await session.execute(
        select(Movie).order_by(Movie.movie_number).offset(offset).limit(per_page)
    )
    return list(result.scalars().all())


async def list_movies_desc(session: AsyncSession, limit: int = 30) -> list[Movie]:
    result = await session.execute(select(Movie).order_by(Movie.movie_number.desc()).limit(limit))
    return list(result.scalars().all())


async def count_movies(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Movie.id)))
    return int(result.scalar() or 0)


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return int(result.scalar() or 0)


async def search_movies_by_title(session: AsyncSession, query: str, limit: int = 50) -> list[Movie]:
    like_query = f"%{query}%"
    result = await session.execute(
        select(Movie)
        .where(or_(Movie.title.ilike(like_query), Movie.title.like(like_query)))
        .order_by(Movie.movie_number)
        .limit(limit)
    )
    return list(result.scalars().all())


async def increment_movie_views(session: AsyncSession, movie_number: int) -> None:
    await session.execute(
        update(Movie)
        .where(Movie.movie_number == movie_number)
        .values(views_count=Movie.views_count + 1)
    )
    await session.commit()


async def delete_movie_by_number(session: AsyncSession, movie_number: int) -> bool:
    movie = await get_movie_by_number(session, movie_number)
    if movie is None:
        return False

    parts_result = await session.execute(select(MoviePart).where(MoviePart.movie_id == movie.id))
    for part in list(parts_result.scalars().all()):
        await session.delete(part)

    await session.delete(movie)
    await session.flush()

    # Keep numbering sequential without gaps.
    result = await session.execute(
        select(Movie).where(Movie.movie_number > movie_number).order_by(Movie.movie_number)
    )
    movies = list(result.scalars().all())
    for item in movies:
        item.movie_number -= 1

    await session.commit()
    return True


async def update_movie_field(
    session: AsyncSession,
    movie_number: int,
    field_name: str,
    value: str | int | None,
) -> bool:
    movie = await get_movie_by_number(session, movie_number)
    if movie is None:
        return False
    setattr(movie, field_name, value)
    await session.commit()
    return True


async def list_first_users(session: AsyncSession, limit: int = 50) -> list[User]:
    result = await session.execute(select(User).order_by(User.id).limit(limit))
    return list(result.scalars().all())


async def get_or_create_bot_settings(session: AsyncSession) -> BotSettings:
    result = await session.execute(select(BotSettings).where(BotSettings.id == 1))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = BotSettings(id=1, force_sub_enabled=False)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


async def set_force_sub_enabled(session: AsyncSession, enabled: bool) -> BotSettings:
    settings = await get_or_create_bot_settings(session)
    settings.force_sub_enabled = enabled
    await session.commit()
    await session.refresh(settings)
    return settings


async def set_force_sub_channel_id(session: AsyncSession, channel_id: int) -> BotSettings:
    settings = await get_or_create_bot_settings(session)
    settings.force_sub_channel_id = channel_id
    await session.commit()
    await session.refresh(settings)
    return settings


async def set_force_sub_channel_link(session: AsyncSession, link: str | None) -> BotSettings:
    settings = await get_or_create_bot_settings(session)
    settings.force_sub_channel_link = link
    await session.commit()
    await session.refresh(settings)
    return settings


async def list_force_sub_channels(session: AsyncSession) -> list[ForceSubChannel]:
    result = await session.execute(
        select(ForceSubChannel).order_by(ForceSubChannel.id.asc())
    )
    return list(result.scalars().all())


async def add_or_update_force_sub_channel(
    session: AsyncSession, channel_id: int, channel_link: str | None
) -> ForceSubChannel:
    result = await session.execute(
        select(ForceSubChannel).where(ForceSubChannel.channel_id == channel_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        item = ForceSubChannel(channel_id=channel_id, channel_link=channel_link)
        session.add(item)
    else:
        item.channel_link = channel_link
    await session.commit()
    await session.refresh(item)
    return item


async def delete_force_sub_channel(session: AsyncSession, row_id: int) -> bool:
    result = await session.execute(
        select(ForceSubChannel).where(ForceSubChannel.id == row_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        return False
    await session.delete(item)
    await session.commit()
    return True


async def add_movie_parts(session: AsyncSession, movie_id: int, file_ids: list[str]) -> None:
    for idx, file_id in enumerate(file_ids, start=1):
        session.add(MoviePart(movie_id=movie_id, part_number=idx, file_id=file_id))
    await session.commit()


async def get_movie_parts(session: AsyncSession, movie_id: int) -> list[MoviePart]:
    result = await session.execute(
        select(MoviePart).where(MoviePart.movie_id == movie_id).order_by(MoviePart.part_number)
    )
    return list(result.scalars().all())


async def replace_movie_parts(
    session: AsyncSession, movie_number: int, file_ids: list[str]
) -> bool:
    movie = await get_movie_by_number(session, movie_number)
    if movie is None or not file_ids:
        return False

    result = await session.execute(select(MoviePart).where(MoviePart.movie_id == movie.id))
    old_parts = list(result.scalars().all())
    for part in old_parts:
        await session.delete(part)
    await session.flush()

    for idx, fid in enumerate(file_ids, start=1):
        session.add(MoviePart(movie_id=movie.id, part_number=idx, file_id=fid))

    # Keep compatibility with places that still read `movies.file_id`
    movie.file_id = file_ids[0]
    await session.commit()
    return True
