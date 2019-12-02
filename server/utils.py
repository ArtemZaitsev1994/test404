import json
import datetime
from typing import Dict

import aioredis
import asyncio
from aiohttp import ClientSession, ClientError

from models import User
from settings import REDIS_HOST, WAIT_BETWEEN_REQUESTS


def get_user(func):
    async def wrap(self):
        """
        Декоратор для вьюх, которые получают одни и те же данные.
        data - данные из запроса.
        user - экземпляр класса для работы с базой данных и коллекцией User.
        """
        data = await self.request.json()
        user = User(self.request.app.db, data['user_name'])
        await user.create_user()
        return await func(self, user, data)
    return wrap


async def check_feailed_mess(app):
    """
    Корутина, которая в фоне выполняет проверку на неотправленные
    сообщения и пытается сделать это еще раз.
    """
    async def send_feailed(app):
        while True:
            failed = await app['redis'].keys('user_*')
            for user_key in failed:
                _, keys = await app['redis'].sscan(user_key)
                for key in keys:
                    m = await app['redis'].get(key)
                    app.loop.create_task(
                        send_to_messenger(app, json.loads(m), key))
            await asyncio.sleep(10)

    app.loop.create_task(send_feailed(app))


async def check_mess(app):
    """
    Запускаем при старте приложения, для того, чтобы перекинуть все сообщения,
    которые были в процессе отправки на момент аварийного отключения приложения,
    на отправку еще раз.
    """
    if await app['redis'].exists('in_process'):
        for key in await app['redis'].spop('in_process'):
            if not await app['redis'].exists(key):
                continue
            data = json.loads((await app['redis'].get(key)).decode("utf-8"))
            app.loop.create_task(
                send_to_messenger(app, data, key))


async def create_redis_pool(app):
    """Создание пула соединений с Redis"""
    # app['redis'] = await aioredis.create_redis_pool('redis://localhost')
    # app['redis'] = await aioredis.create_redis_pool('redis://redis')
    app['redis'] = await aioredis.create_redis_pool(REDIS_HOST)


async def on_cleanup(app):
    """Закрытие соединений с Redis"""
    app['redis'].close()
    await app['redis'].wait_closed()


async def send_to_messenger(app, data: Dict, key: str):
    """
    Отправляет сообщения на сервер мессенджеров,
    запускается в фоне.
    """
    await app['redis'].sadd('in_process', key)
    if data['time'] is not None:
        delta = datetime.datetime(*data['time']) - datetime.datetime.now()
        if delta.total_seconds() > 0:
            await asyncio.sleep(delta.total_seconds())
    url = data.pop('url')
    async with ClientSession() as session:
        success = False
        for i in range(app['retries_times']):
            try:
                async with session.post(url, json=data) as req:
                    if req.status == 200:
                        success = True
                        await app['redis'].srem('in_process', key)
                        await app['redis'].delete(key)
                        await app['redis'].srem(f'user_{data["sender"]}', key)
                        break
            except ClientError as e:
                print(repr(e))
                await asyncio.sleep(WAIT_BETWEEN_REQUESTS)
        if not success:
            await app['redis'].srem('in_process', key)
            await app['redis'].sadd(f'user_{data["sender"]}', key)
