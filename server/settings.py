from os.path import isfile
from envparse import env


if isfile('.env'):
    env.read_envfile('.env')

WEB_ADRESSES = env.str('WEB_ADRESSES')
MESSENGER_HOST = env.int('MESSENGER_HOST')
RETRIES_TIMES = env.str('RETRIES_TIMES')
# MONGO_HOST = 'mongodb'
MONGO_HOST = env.str('MONGO_HOST')
MONGO_DB_NAME = env.str('MONGO_DB_NAME')
