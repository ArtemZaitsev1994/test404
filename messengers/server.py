from aiohttp import web

from views import Telegram, WhatsApp, Viber


app = web.Application()
app.router.add_route('*', '/telegram', Telegram)
app.router.add_route('*', '/whatsapp', WhatsApp)
app.router.add_route('*', '/viber', Viber)

web.run_app(app, port=8081)
