import json
import re
from datetime import datetime

import aiohttp
import asyncio

from utils import get_delay_time


HOST = 'http://0.0.0.0:8080'
ERROR_MESS = 'Что-то не так, попробуйте пингануть сервер или изменить запрос.'
COMMANDS = '''
	Добавить пользователя...............1
	Отправить сообщение пользователю....2
	Удалить пользователя................3
	Выход...............................4
'''


def query_decor(link, method):
	def wrap(func):
		async def wrap_func(session):
			data = await func(session)
			if data is None:
				return
			async with session.request(method, link, json=data) as req:
				if req.status == 200:
					res_data = json.loads(await req.text())
					message = res_data['message']
					print('--------------------ANSWER--------------------')
					print(message)
					print('----------------------------------------------')
				else:
					print(ERROR_MESS)
		return wrap_func
	return wrap


async def main():
	async with aiohttp.ClientSession() as session:
		while True:
			print(COMMANDS)
			command = input('\nEnter command: ')
			print(command)
			if command in commands:
				await commands[command](session)
			else:
				print('Такой команды нет\n')


@query_decor(f'{HOST}/api/contacts', 'post')
async def add_user(session):
	name = input('Имя контакта (пустая строка для отмены): ')
	if not name:
		return
	contact = {
		'name': name,
		'messangers': 
			{
			'telegram': input('Ник или номер в Telegram (пустая строка для пропуска): '),
			'whatsApp': input('Номер в WhatsApp (пустая строка для пропуска): '),
			'viber': input('Номер в Viber (пустая строка для пропуска): '),
		}
	}

	return ({'user_name': user_name, 'contact': contact, 'name': name})


@query_decor(f'{HOST}/api/contacts', 'delete')
async def rm_user(session):
	contacts = await get_contacts(session)
	if contacts:
		contact = input('Выберите кого хотите удалить: ')
		if not contact or contact not in contacts:
			return
		return {'user_name': user_name, 'contact': contact}


@query_decor(f'{HOST}/api/contacts', 'put')
async def send_mess(session):
	contacts = await get_contacts(session)
	if contacts:
		input_contacts = input('Выберите кому хотите отправить сообщение\n(Например: Иван, Маша, Катя): ')
		result_contact = []
		if not input_contacts:
			return
		for contact in input_contacts.split(', '):
			if contact not in contacts:
				print(f'Нет такого контакта {contact}')
			else:
				result_contact.append(contact)
		if len(result_contact) <= 0:
			return
		message = input('Введите сообщение: ')
		if message == '':
			return
		time = get_delay_time()
		if time is not None:
			time = [
				time.year,
				time.month,
				time.day,
				time.hour,
				time.minute,
				time.second
			]

		data = {
			'user_name': user_name,
			'contacts': result_contact,
			'message': message,
			'time': time
		}

		return data
	else:
		print('У вас нет контактов.')


async def get_contacts(session):

	async with session.request('get', f'{HOST}/api/contacts', json={'user_name': user_name}) as req:
		contacts = {}
		if req.status == 200:
			res_data = json.loads(await req.text())
			contacts = res_data['contacts']
			print('--------------------ANSWER--------------------')
			print('Ваши контакты:')
			for name, data in res_data['contacts'].items():
				print(f'{name}:\n')
				no_messengers = True
				for messanger, value in data.items():
					if value:
						no_messengers = False
						print(f'\t{messanger} - {value}')
				if no_messengers:
					print('\tУ контакта не заданы мессенджеры')
			print('----------------------------------------------')
		else:
			print(ERROR_MESS)
		return contacts


if __name__ == '__main__':
	commands = {
		'1': add_user,
		'2': send_mess,
		'3': rm_user,
		'4': quit
	}
	user_name = input('Введите свой ник: ')
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
