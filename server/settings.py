from os.path import isfile
from envparse import env


if isfile('.env'):
    env.read_envfile('.env')

MESSENGER_HOST = env.str('MESSENGER_HOST')
RETRIES_TIMES = env.int('RETRIES_TIMES')
MONGO_HOST = env.str('MONGO_HOST')
MONGO_DB_NAME = env.str('MONGO_DB_NAME')
REDIS_HOST = env.str('REDIS_HOST')
WAIT_BETWEEN_REQUESTS = env.int('WAIT_BETWEEN_REQUESTS')
