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
	Проверить доставку сообщений........4
	Выход...............................5
'''
SUCCESS_ANSWERS = {
    'post': 'Контакт был успешно создан.',
    'put': 'Сообщение было добавлено в очердь на отправку.',
    'delete': 'Контакт был успешно удален.',
}
FAIL_ANSWERS = {
    'post': 'Ошибка. Контакт НЕ был создан',
    'put': 'Ошибка. Сообщение НЕ было добавлено в очердь на отправку.',
    'delete': 'Ошибка. Контакт НЕ был удален.',
    'get': 'У вас нет контактов.',
}


def query_decor(method):
    def wrap(func):
        LINK = f'{HOST}/api/contacts'

        async def wrap_func(session):
            data = await func(session)
            if data is None:
                return
            async with session.request(method, LINK, json=data) as req:
                print('--------------------ANSWER--------------------')
                if req.status == 200 and json.loads(await req.text())['success']:
                    print(SUCCESS_ANSWERS[method])
                else:
                    print(FAIL_ANSWERS[method])
                print('----------------------------------------------')
        return wrap_func
    return wrap


async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            print(COMMANDS)
            command = input('\nEnter command: ')
            if command in commands:
                await commands[command](session)
            else:
                print('Такой команды нет\n')


@query_decor('post')
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

    return ({'user_name': user_name, 'contact': contact})


@query_decor('delete')
async def rm_user(session):
    contacts = await get_contacts(session)
    if contacts:
        contact = input('Выберите кого хотите удалить: ')
        if not contact or contact not in contacts:
            return
        return {'user_name': user_name, 'contact': contact}


@query_decor('put')
async def send_mess(session):
    contacts = await get_contacts(session)
    if not contacts:
        return
    input_contacts = input(
        'Выберите кому хотите отправить сообщение\n(Например: Иван, Маша, Катя): ')
    if not input_contacts:
        return
    result_contact = []
    for contact in input_contacts.split(', '):
        if contact not in contacts:
            print(f'Нет такого контакта {contact}')
        else:
            result_contact.append(contact)
    if len(result_contact) <= 0:
        print('Не были выбраны контакты.')
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
    print(f'Отправлен запрос для: {result_contact}')
    return data


async def get_contacts(session):

    async with session.request('get', f'{HOST}/api/contacts', json={'user_name': user_name}) as req:
        contacts = {}
        print('--------------------ANSWER--------------------')
        if req.status == 200:
            res_data = json.loads(await req.text())
            contacts = res_data['contacts']
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
        else:
            print(FAIL_ANSWERS['get'])
        print('----------------------------------------------')
        return contacts


async def get_feiled_mess(session):
    async with session.request('get', f'{HOST}/api/get_failed_mess', json={'user_name': user_name}) as req:
        if req.status == 200:
            data = json.loads(await req.text())
            if data['data']:
                print('Не отправленные сообщения:')
                print('-------------------------------')
                for m in data['data']:
                    mg = m['url'].split('/')[-1]
                    print(f'Кому: {m["contact"]}\nТекст: {m["message"]}\nМессенджер: {mg}')
                    print('-------------------------------')
            else:
                print('Все сообщения успешно отправлены!')


if __name__ == '__main__':
    commands = {
        '1': add_user,
        '2': send_mess,
        '3': rm_user,
        '4': get_feiled_mess,
        '5': quit,
    }
    user_name = input('Введите свой ник: ')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
