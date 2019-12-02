import datetime
import pytest
import json
import uuid
import aioredis
from aiohttp import web
from motor import motor_asyncio as ma

from utils import send_to_messenger
from routes import routes
from models import User


MONGO_HOST = 'mongodb://127.0.0.1:27017'
MONGO_DB_NAME = '404test'
RETRIES_TIMES = 2  # количество повторов отправки сообщения при ошибке
TEST_DATA = [{
    'name': 'Sasha',
    'messengers' : {
        'telegram': 'Alexandrov',
        'whatsApp': '89926655332',
        'viber': 'viber_id',
    },

},
{
    'name': 'Ivan',
    'messengers' : {
        'telegram': 'Ivanov',
        'whatsApp': '+79508465333',
        'viber': 'viber_id',
    },

}]


async def create_redis_pool(app):
    app['redis'] = await aioredis.create_redis_pool('redis://localhost')


async def on_cleanup(app):
    await cli.app['redis'].flushdb()    
    app['redis'].close()
    await app['redis'].wait_closed()


async def create_user(app):
    app['user_db'] = User(app.db, 'Artem')
    await app['user_db'].clear_db()
    await app['user_db'].create_user()
    await app['user_db'].add_contact(TEST_DATA[0])
    await app['user_db'].add_contact(TEST_DATA[1])


@pytest.fixture
def cli(loop, aiohttp_client):
    app = web.Application()
    for route in routes:
        app.router.add_route(*route)

    app.client = ma.AsyncIOMotorClient(MONGO_HOST)
    app.db = app.client[MONGO_DB_NAME]
    app['retries_times'] = RETRIES_TIMES

    app.on_startup.append(create_redis_pool)
    app.on_startup.append(create_user)

    app.on_cleanup.append(on_cleanup)
    return loop.run_until_complete(aiohttp_client(app))


async def test_add_contact(cli):
    """Тест на добавление контакта к пользователю"""
    data = {
        'user_name': 'Artem',
        'contact': {
            'name': 'Valera',
            'messengers': {
                'telegram': 'Val',
                'whatsApp': '',
                'viber': '',
            }
        }
    }
    result_in_db = {
        'telegram': 'Val',
        'whatsApp': '',
        'viber': '',
    }
    resp = await cli.post('/api/contacts', json=data)
    assert resp.status == 200
    answer = json.loads(await resp.text())
    assert answer['success'] is True
    user = await cli.app['user_db'].check_user()
    user.pop('_id')
    assert user['contacts']['Valera'] == result_in_db


async def test_delete_contact(cli):
    """Тест на удаление контакта у пользователя"""
    data = {
        'user_name': 'Artem',
        'contact': 'Sasha',
    }
    resp = await cli.delete('/api/contacts', json=data)
    assert resp.status == 200
    answer = json.loads(await resp.text())
    assert answer['success'] is True
    assert await User(cli.app.db, 'Artem').get_contacts() == {
        'Ivan' : {
            'telegram': 'Ivanov',
            'whatsApp': '+79508465333',
            'viber': 'viber_id',
        },

    }


async def test_send_message_to_messengers(cli):
    """Тест на отправку сообщения в мессенджеры"""
    HOST = 'http://0.0.0.0:8081/'
    adresses = {
        'telegram': f'{HOST}telegram',
        'whatsApp': f'{HOST}whatsapp',
        'viber': f'{HOST}viber'
    }
    redis_data = [{
        'sender': 'Artem',
        'message': 'Тест отправки сообщения в мессенджеры.',
        'contact': 'Ivan',
        'url': '',
        'time': [2019, 12, 1, 16, 41, 22]
    },
    {
        'sender': 'Artem',
        'message': 'Тест отправки сообщения в мессенджеры.',
        'contact': 'Sasha',
        'url': '',
        'time': None
    }]
    for t in redis_data:
        for adr in adresses.values():
            t['url'] = adr
            key = str(uuid.uuid4())
            await cli.app['redis'].set(key, json.dumps(t))
            await send_to_messenger(cli.app, t, key)
    assert await cli.app['redis'].scard('user_Artem') == 2
    await cli.app['redis'].flushdb()    


async def test_send_delayed_message_to_messengers(cli):
    """Тест на отправку отложенного (на 10 секунд) сообщения в мессенджеры"""
    planned_time = datetime.datetime.now() + datetime.timedelta(seconds=10)
    data = {
        'sender': 'Artem',
        'message': 'Тест отправки сообщения в мессенджеры.',
        'contact': 'Ivan',
        'url': 'http://0.0.0.0:8081/whatsapp',
        'time': [
            planned_time.year,
            planned_time.month,
            planned_time.day,
            planned_time.hour,
            planned_time.minute,
            planned_time.second,
        ]
    }
    key = str(uuid.uuid4())
    await cli.app['redis'].set(key, json.dumps(data))
    await send_to_messenger(cli.app, data, key)
    assert datetime.datetime.now() + datetime.timedelta(seconds=1) > planned_time
    await cli.app['redis'].flushdb()
