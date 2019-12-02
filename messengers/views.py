from aiohttp import web


ANSWER = "Cообщение принято"


class Telegram(web.View):
    async def post(self):
        """Endpoint для приема сообщений из Telegram"""
        data = await self.request.json()
        print('Telegram ', data)
        return web.json_response({'message': ANSWER})


class WhatsApp(web.View):
    """Endpoint для приема сообщений из WhatsApp"""
    async def post(self):
        data = await self.request.json()
        print('WhatsApp ', data)
        return web.json_response({'message': ANSWER})


class Viber(web.View):
    """
    Endpoint для приема сообщений из Viber.
    ВСЕГДА отвечает ОШИБКОЙ.
    """
    async def post(self):
        data = await self.request.json()
        print('Viber ', data)
        return web.json_response({}, status=500)
