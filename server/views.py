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
        await self.request.app['redis'].set('test', 'test')
        return web.json_response({'success': bool(result), 'q': (await self.request.app['redis'].get('test')).decode('utf-8')})

    @get_user
    async def get(self, user: User, data: Dict[str, str]):
        contacts = await user.get_contacts()
        return web.json_response({'contacts': contacts})

    @get_user
    async def put(self, user: User, data: Dict[str, str]):
        contact = await user.check_user()
        success = True
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
                        success = False
                    else:
                        self.request.app.loop.create_task(
                            send_to_messanger(self.request.app, redis_data, key))
        return web.json_response({'success': success})

    @get_user
    async def delete(self, user: User, data: Dict[str, str]):
        result = await user.remove_contact(data['contact'])
        return web.json_response({'success': bool(result)})


class Info(web.View):
    @get_user
    async def get(self, user: User, data: Dict[str, str]):
        failed = [json.loads((await self.request.app['redis'].get(x)).decode('utf-8'))
                  for x
                  in (await self.request.app['redis'].sscan(f'user_{user.name}'))[1]
                  if x is not None]

        return web.json_response({'data': failed})
