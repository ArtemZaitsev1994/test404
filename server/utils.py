import json
import datetime

import aioredis
import asyncio
from aiohttp import ClientSession, ClientError

from models import User


def get_user(func):
	async def wrap(self):
		data = await self.request.json()
		user = User(self.request.app.db, data['user_name'])
		await user.create_user()
		return await func(self, user, data)
	return wrap


async def check_feailed_mess(app):
	async def send_feailed(app):
		while True:
			failed = await app['redis'].keys('user_*')
			for key in failed:
				for i in range(await app['redis'].llen(key)):
					m_key = await app['redis'].lpop(key)
					m = await app['redis'].get(m_key)
					app.loop.create_task(send_to_messanger(app, json.loads(m), m_key))
			await asyncio.sleep(10)

	app.loop.create_task(send_feailed(app))


async def check_mess(app):
	_, keys = await app['redis'].sscan('in_process')
	for key in keys:
		data = json.loads((await app['redis'].get(key)).decode("utf-8"))
		await app['redis'].rpush(f'user_{data["sender"]}', key)
	await app['redis'].delete('in_process')


async def create_redis_pool(app):
	# app['redis'] = await aioredis.create_redis_pool('redis://localhost')
	app['redis'] = await aioredis.create_redis_pool('redis://redis')


async def on_cleanup(app):
	app['redis'].close()
	await app['redis'].wait_closed()


async def send_to_messanger(app, data, key):
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
						print('отправлено')
						await app['redis'].srem('in_process', key)
						await app['redis'].delete(key)
						break
			except ClientError as e:
				print(repr(e))
				await asyncio.sleep(3)
		if not success:
			await app['redis'].srem('in_process', key)
			await app['redis'].rpush(f'user_{data["sender"]}', key)
