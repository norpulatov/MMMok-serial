import logging

import httpx


logger = logging.getLogger(__name__)


async def serve_foyda_ads(api_key: str, user_id: int) -> None:
    if not api_key:
        return
    url = f"https://api.foydaads.uz/api/serve/{api_key}?user_id={user_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
        if response.status_code != 200:
            logger.info("FoydaAds skipped: non-200 status=%s", response.status_code)
            return
        data = response.json()
        if data.get("status") == "ok":
            logger.info("FoydaAds served successfully. ad_id=%s", data.get("ad_id"))
            return
        logger.info("FoydaAds skipped: %s", data.get("message"))
    except Exception:
        logger.exception("Error connecting to FoydaAds")
