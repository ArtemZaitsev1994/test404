import json
import uuid
from typing import Dict

from aiohttp import web, ClientSession
from aiohttp.web import middleware

from schemas import SCHEMAS
from models import User
from utils import get_user, send_to_messanger


# HOST = 'http://0.0.0.0:8081'
HOST = 'http://messengers_server:8081'

WEB_ADRESSES = {
    'telegram': f'{HOST}/telegram',
    'whatsApp': f'{HOST}/whatsapp',
    'viber': f'{HOST}/viber'
}


class Handler(web.View):
    @get_user
    async def post(self, user: User, data: Dict[str, str]):
        """Создание контакта у пользователя."""
        result = await user.add_contact(data['contact'])
        await self.request.app['redis'].set('test', 'test')
        return web.json_response({'success': bool(result), 'q': (await self.request.app['redis'].get('test')).decode('utf-8')})

    @get_user
    async def get(self, user: User, data: Dict[str, str]):
        """Запрос на получение всех контактов пользователя."""
        contacts = await user.get_contacts()
        return web.json_response({'contacts': contacts})

    @get_user
    async def put(self, user: User, data: Dict[str, str]):
        """
        Запрос на отправку сообщения в мессенджеры.
        Вьюха создает задачу в фоне.
        """
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
                        # Здесь создаем задачу в фоне
                        self.request.app.loop.create_task(
                            send_to_messanger(self.request.app, redis_data, key))
        return web.json_response({'success': success})

    @get_user
    async def delete(self, user: User, data: Dict[str, str]):
        """Удаление контакта у пользователя."""
        result = await user.remove_contact(data['contact'])
        return web.json_response({'success': bool(result)})


class Info(web.View):
    @get_user
    async def get(self, user: User, data: Dict[str, str]):
        """Получение сообщений, которые не удалось отправить."""
        failed = [json.loads((await self.request.app['redis'].get(x)).decode('utf-8'))
                  for x
                  in (await self.request.app['redis'].sscan(f'user_{user.name}'))[1]
                  if x is not None]

        return web.json_response({'data': failed})
