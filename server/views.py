import json
import uuid
from typing import Dict

from aiohttp import web, ClientSession

from models import User
from utils import get_user, send_to_messanger


WEB_ADRESSES = {
	'telegram': 'http://0.0.0.0:8081/telegram',
	'whatsApp': 'http://0.0.0.0:8081/whatsapp',
	'viber': 'http://0.0.0.0:8081/viber'
}


class Handler(web.View):
	@get_user
	async def post(self, user: User, data: Dict[str, str]):
		result = await user.add_contact(data['contact'])
		message = f'Contact {data["name"]} has been added.' if result else ''
		return web.json_response({'message': message})

	@get_user
	async def get(self, user: User, data: Dict[str, str]):
		# await user.clear_db()
		contacts = await user.get_contacts()
		return web.json_response({'contacts': contacts})

	@get_user
	async def put(self, user: User, data: Dict[str, str]):
		contact = await user.check_user()
		for c in data['contacts']:
			addressee = contact['contacts'][c]
			for messanger, value in addressee.items():
				if value:
					redis_data = {
						'sender': user.name,
						'message': data['message'],
						'contact': c,
						'url': WEB_ADRESSES[messanger],
						'time': data['time']
					}
					key = str(uuid.uuid4())
					try:
						await self.request.app['redis'].set(key, json.dumps(redis_data))
					except Exception as e:
						print('Published failed', e)
					else:
						self.request.app.loop.create_task(send_to_messanger(self.request.app, redis_data, key))


		message = 'The message has been added to the queue for sending.'
		return web.json_response({'message': message})

	@get_user
	async def delete(self, user: User, data: Dict[str, str]):
		result = await user.remove_contact(data['contact'])
		if result is None:
			message = 'Contact not found.'
		else:
			message = 'The contact has been removed from the contact list.'
		return web.json_response({'message': message})


class Info(web.View):
	@get_user
	async def get(self, user: User, data: Dict[str, str]):
		message = 'No delivery failures.'
		failed = await self.request.app['redis'].llen(f'user_{user.name}')
		messages = []
		for i in range(failed):
			key = await self.request.app['redis'].lpop(f'user_{user.name}')
			m = await self.request.app['redis'].get(key)
			messages.append(m.decode('utf-8'))
			await self.request.app['redis'].rpush(f'user_{user.name}', m)
		if len(messages) > 0:
			message = f'Failed {len(messages)} messages.'

		return web.json_response({'data': messages, 'message': message})
