from aiohttp import web


ANSWER = """
Cообщение принято
"""


class Telegram(web.View):
	async def post(self):
		data = await self.request.json()
		print('Telegram ', data)
		return web.json_response({'message': ANSWER})


class WhatsApp(web.View):
	async def post(self):
		data = await self.request.json()
		print('WhatsApp ', data)
		return web.json_response({'message': ANSWER})


class Viber(web.View):
	async def post(self):
		data = await self.request.json()
		print('Viber ', data)
		return web.json_response({}, status=500)
