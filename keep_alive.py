import asyncio
from aiohttp import web
from threading import Thread


async def handle(request):
    return web.Response(text="I'm alive!")


async def start_app():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8000)
    await site.start()


def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_app())
    loop.run_forever()


def keep_alive():
    t = Thread(target=run)
    t.start()
