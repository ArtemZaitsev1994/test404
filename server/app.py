from aiohttp import web
from motor import motor_asyncio as ma

from views import Handler, Info
from utils import on_cleanup, create_redis_pool, check_mess, check_feailed_mess


MONGO_HOST = 'mongodb://127.0.0.1:27017'
# MONGO_HOST = 'mongodb://mongodb:27017'
MONGO_DB_NAME = '404'
RETRIES_TIMES = 1

app = web.Application()
app.router.add_route('*', '/api/contacts', Handler)
app.router.add_route('GET', '/api/get_failed_mess', Info)

app.client = ma.AsyncIOMotorClient(MONGO_HOST)
app.db = app.client[MONGO_DB_NAME]
app['retries_times'] = RETRIES_TIMES

app.on_startup.append(create_redis_pool)
app.on_startup.append(check_mess)
app.on_startup.append(check_feailed_mess)
app.on_cleanup.append(on_cleanup)
web.run_app(app)
