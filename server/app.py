from aiohttp import web
from motor import motor_asyncio as ma

from utils import on_cleanup, create_redis_pool, check_mess, check_feailed_mess
from routes import routes
from settings import RETRIES_TIMES, MONGO_HOST, MONGO_DB_NAME


# MONGO_HOST = 'mongodb://127.0.0.1:27017'
# MONGO_HOST = 'mongodb://mongodb:27017'
# MONGO_DB_NAME = '404'
# RETRIES_TIMES = 1

app = web.Application()
for route in routes:
    app.router.add_route(*route)

app.client = ma.AsyncIOMotorClient(MONGO_HOST)
app.db = app.client[MONGO_DB_NAME]
app['retries_times'] = RETRIES_TIMES

app.on_startup.append(create_redis_pool)
app.on_startup.append(check_mess)
app.on_startup.append(check_feailed_mess)

app.on_cleanup.append(on_cleanup)

web.run_app(app)
