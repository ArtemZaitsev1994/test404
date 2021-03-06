# Тестовое задание "Микросервис рассылки сообщений в мессенджеры".

Проект состоит из микросервиса, эмулятора сервера для приема сообщейни и cli-клиента.

## Логика работы
Сервер может принимать запросы с json-данными из клиента или непосредственно из строки (список запросов и примеры ниже). Для начала, пользователь создает список своих контактов. Потом уже пользователь может попросить сервер разослать во все указанные мессенджеры сообщения одному выбранному контакту (или группе контактов). 
Реализован только механизм идентификации(пользователь указывает свое имя в запросе); аутентификация и авторизация на данном этапе отсутствуют.

## Техническое описание
Микросервис реализован на python с применением aiohttp фреймворка. Aiohttp является одним из самых быстрых фреймворков для python достигших production стадии разработки. 

Имена пользователей и их контакты хранятся в базе данных MongoDB. Эта документоориентированная база данных удобна для хранения цельных объектов не имеющих реляционных отношений к другим записям. Таким образом, за один запрос мы достаем из базы всю нам нужную информацию в кратчайший срок. В иной бизнес-модели стоит пересмотреть выбор базы данных.

Сами сообщения хранятся в Redis. Одна из самых быстрых in-memory баз данных обеспечит эффективный доступ к сообщениям. В целом, нам не нужно хранить сообщения - микросервис выполняет роль proxy-сервера, который просто пересылает сообщения на нужные нам мессенджеры. Но для предотвращения потери сообщений, помимо стандартных настроек бэкапа, была добавлена запись в фаил настроек Redis (etc/redis/redis.conf):
> slowlog-log-slower-than 0

которая обеспечит логирование всех обращений к базе.

Тестовый сервер, на который проксируются все сообщения, выполнен также на aiohttp и имеет 3 условные endpoint'a. Telegram, WhatsApp и Viber, при чем Viber **ВСЕГДА** отвечает ошибкой.

Перменные окружения для приложения указаны в /server/.env файле.
* `MONGO_HOST` - Хост базы данных MongoDB
* `MONGO_DB_NAME` - Имя рабочей базы данных
* `RETRIES_TIMES` - Количество повторов при неудачной отправке сообщений
* `MESSENGER_HOST` - Хост сервера с мессенджерами
* `REDIS_HOST` - Адрес Redis-server
* `WAIT_BETWEEN_REQUESTS` - Время между попытками отправить запрос (секунд)

## Запуск приложения
Приложение, Redis, MongoDB и фиктивный сервер разворачиваются в докере.
Клонируйте репозиторий.
> git clone https://github.com/ArtemZaitsev1994/test404.git

Перейдите в папку с проектом.
> cd test404

Запустите сборку Docker-compose
> sudo docker-compose up --build -d

Сервер будет доступен по `localhost:8080`
Если развернуть проект не в режиме демона (флаг -d), то можно видеть как приходят сообщения на сервер.

## API
### Создание контакта:
#### Curl пример
```
curl --header "Content-Type: application/json" --request POST --data '{"user_name": "test", "contact": {"name": "Artem", "messengers": {"telegram": "ArtemZaitsev", "whatsApp": "+799200828615", "viber": ""}}, "name": "Artem"}' http://localhost:8080/api/contacts
```
#### URL
`http://localhost:8080/api/contacts`
#### JSON request data
```
{
  "user_name": str,
  "contact": {
    "name": str,
    "messengers": {
      "telegram": str,
      "whatsApp": str,
      "viber": str
    },
  }
}
```
* `user_name` - Имя, под которым выполняется запрос.
* `contact.name` - имя контакта, который хотим добавить.
* `contact.messengers.telegram` - ID в Telegram
* `contact.messengers.whatsApp` - ID в WhatsApp
* `contact.messengers.viber` - ID в Viber

#### Response
```
{'success': bool}
```

### Удаление контакта:
#### Curl пример
```
curl --header "Content-Type: application/json" --request DELETE --data '{"user_name": "test", "contact": "Artem"}' http://localhost:8080/api/contacts
```
#### URL
`http://localhost:8080/api/contacts`
#### JSON request data
```
{
  'user_name': str,
  'contact': str
}
```
* `user_name` - Имя, под которым выполняется запрос.
* `contact` - имя контакта, который хотим удалить.

#### Response
```
{'success': bool}
```

### Отправка сообщений:
#### Curl пример
```
curl --header "Content-Type: application/json" --request PUT --data '{"user_name": "test", "contacts": ["Artem", "Lera", "Vasya"], "message": "Hello there", "time": [2019, 11, 30, 14, 0, 6]}' http://localhost:8080/api/contacts
```
#### URL
`http://localhost:8080/api/contacts`
#### JSON request data
```
{
  'user_name': str,
  'contacts': list[name: str, ...],
  'message': str,
  'time': list[int, int, int, int, int, int],
}
```
* `user_name` - Имя, под которым выполняется запрос.
* `contact` - список имён контактов, кому хотим отправить сообщение.
* `message` - текст сообщения.
* `time` - время, не раньше которого нужно начать отправку (текущее или раньше, чтобы отправить при получении).

#### Response
```
{
  'success': bool,
  'wrong_contacts': [{
    'name': str,
    'error': str,
  }, ...]
}
```
* `success` - булево значение, возвращает True, только если сообщения удачно разосланы всем контактам.
* `wrong_contacts` - список контактов, кому не удалось разослать сообщения.
* `wrong_contacts.name` - имя контакта.
* `wrong_contacts.error` - текст ошибки.

### Получить список своих контактов:
#### Curl пример
```
curl --header "Content-Type: application/json" --request GET --data '{"user_name": "test"}' http://localhost:8080/api/contacts
```
#### URL
`http://localhost:8080/api/contacts`
#### JSON request data
```
{
  'user_name': str,
}
```
* `user_name` - Имя, под которым выполняется запрос.
#### Response
```
{
  'contacts': {
    name: {
      'telegram': str,
      'whatsApp': str,
      'viber': str,
    },
  }
}
```
* `contacts` - словарь контактов, ключами в котором являются имена контактов.
* `contacts[name].telegram` - идентификатор в Telegram.
* `contacts[name].whatsApp` - идентификатор в WhatsApp.
* `contacts[name].viber` - идентификатор в Viber.

### Получить недоставленные сообщения:
#### Curl пример
```
curl --header "Content-Type: application/json" --request GET --data '{"user_name": "test"}' http://localhost:8080/api/get_failed_mess
```
#### URL
`http://localhost:8080/api/get_failed_mess`
#### JSON request data
```
{
  'user_name': str,
}
```
* `user_name` - Имя, под которым выполняется запрос.
#### Response
```
{
  'data': {
    'sender': 'test',
    'message': 'f',
    'contact': 'asd',
    'url': 'http://0.0.0.0:8081/viber',
    'time': [2019, 11, 30, 13, 19, 18]
  }
}
```
* `data.sender` - юзер из под которого было создано сообщение.
* `data.message` - текст сообщения.
* `data.contact` - имя контакта, которому было адресовано сообщение.
* `data.url` - адрес сервиса, на который была попытка отправить.
* `data.time` - время, на которое было назначена отправка.

## Тесты
Для приложения подготовлены небольшие тесты. Тесты следует запускать при развернутом в Docker приложении, чтобы работа проводилась с развернутыми базами данных в контейнерах, дабы избежать потери данных.

Разоваричаем проект:
> sudo docker-compose up --build -d

Останавливаем сервер:
> sudo docker server stop

Переходим в папку с тестами:
> cd server

Запускаем тесты:
> pytest -s -v test.py
