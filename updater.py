try:
    import aiohttp
    AIO_OK = True
except ImportError:
    AIO_OK = False

try:
    from bs4 import BeautifulSoup
    BS_OK = True
except ImportError:
    BS_OK = False


async def _fetch(url, timeout=10):
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0"}) as r:
            return await r.text()


def обновить_синхронно(url, селекторы=None):
    if not AIO_OK:
        return None
    try:
        import asyncio
        html = asyncio.run(_fetch(url))
        if not BS_OK:
            return None
        soup = BeautifulSoup(html, "html.parser")
        if селекторы:
            try:
                s = float(soup.select_one(селекторы["scored"]).text.strip())
                c = float(soup.select_one(селекторы["conceded"]).text.strip())
                return s, c
            except (AttributeError, ValueError):
                pass
        return None
    except Exception:
        return None