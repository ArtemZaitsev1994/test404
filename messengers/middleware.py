import logging

from aiohttp.web import middleware


logging.basicConfig(filename="logs.log", level=logging.INFO)

@middleware
async def log_requests(request, handler):

    logging.info(f"Informational message {request}")