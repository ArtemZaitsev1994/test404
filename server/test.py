import pytest
import json
from aiohttp import web
from motor import motor_asyncio as ma

from views import Handler, Info
from utils import on_cleanup, create_redis_pool
from routes import routes
from models import User


MONGO_HOST = 'mongodb://127.0.0.1:27017'
# MONGO_HOST = 'mongodb://mongodb:27017'
MONGO_DB_NAME = '404test'
RETRIES_TIMES = 1


async def create_user(app):
    data = [{
        'name': 'Sasha',
        'messangers' : {
            'telegram': 'Alexandrov',
            'whatsApp': '89926655332',
            'viber': 'viber_id',
        },
    
    },
    {
        'name': 'Ivan',
        'messangers' : {
            'telegram': 'Ivanov',
            'whatsApp': '+79508465333',
            'viber': 'viber_id',
        },

    }]
    app['user_db'] = User(app.db, 'Artem')
    await app['user_db'].clear_db()
    await app['user_db'].create_user()
    await app['user_db'].add_contact(data[0])
    await app['user_db'].add_contact(data[1])


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
            'messangers': {
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
    contacts = await cli.app['user_db'].get_contacts()
    assert await User(cli.app.db, 'Artem').get_contacts() == {
        'Ivan' : {
            'telegram': 'Ivanov',
            'whatsApp': '+79508465333',
            'viber': 'viber_id',
        },

    }


async def test_send_message(cli):
    """Тест на добавление контакта к пользователю"""
    data = {
        'user_name': 'Artem',
        'contacts': ['Ivan', 'Sasha'],
        'message': 'Hello, World!',
        'time': None,
    }
    resp = await cli.put('/api/contacts', json=data)
    assert resp.status == 200
    answer = json.loads(await resp.text())
    assert answer['success'] is True
    # user = await cli.app['user_db'].check_user()
    # user.pop('_id')
    # assert user == result_in_db


async def test_ping_server(cli):
    # пингуем сервер
    # resp = await cli.get('/api/ping')
    # assert resp.status == 200
    # answer = json.loads(await resp.text())
    assert "pong" == 'pong'


# async def test_get_all_accounts(cli):
#     # получаем все акккаунты из базы
#     resp = await cli.get('/api/accounts')
#     assert resp.status == 200
#     answer = json.loads(await resp.text())
#     assert answer['status'] == 200

# async def test_get_all_accounts_from_empty_base(cli):
#     # проверка на ответ из пустой базы
#     async with cli.app['db'].acquire() as conn:
#         await conn.fetch(text('TRUNCATE accounts;'))
#     resp = await cli.get('/api/accounts')
#     assert resp.status == 200
#     answer = json.loads(await resp.text())
#     assert 'No accounts in base.' == answer['description']['message']


# async def test_add_money_to_account(cli):
#     # тест на увелечение баланса
#     # берем идентификатор из тестовых данных
#     uuid = '26c940a1-7228-4ea2-a3bc-e6460b172040'
#     # добавляем денег на счет
#     resp = await cli.post('api/add', json={'uuid': uuid, 'balance': 100})
#     assert resp.status == 200
#     answer = json.loads(await resp.text())
#     assert answer['description']['message'] == f'New balance for account {uuid} is 1800.'


