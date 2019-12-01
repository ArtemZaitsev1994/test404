import datetime
import calendar
import re


INPUT_MESSAGE = """
Введите время, на сколько отложить отправку, в формате hh:mm:ss.
Время будет прибавлено к текущему.
Или введите "дата", чтобы указать конкретную дату сообщения
Введите "выход" для отмены.:
"""


def get_delay_time():
	time = []
	while True:
		time_input = input(INPUT_MESSAGE)
		if time_input == 'дата':
			time = input_date()
			break
		else:
			time = format_delay_time(time_input)
			if time is not None:
				break
	return time


def input_date():
	while True:
		today = datetime.datetime.now()
		print('        _______')
		print('Введите "выход" для отмены.')
		print('        ^^^^^^^')

		year = input_year(today.year)
		if year is None:
			break
		month = input_mounth(today.month)
		if month is None:
			break
		day = input_day(today.year, today.month, today.day)
		if day is None:
			break
		hour = input_hour(0)
		if hour is None:
			break
		minute = input_minute(0)
		if minute is None:
			break
		seconds = input_seconds(0)
		if seconds is None:
			break
		time = datetime.datetime(year, month, day, hour, minute, seconds)
		if time < today:
			print(f'Вы ввели {time}')
			print('Ошибка. Указано прошедшее время.')
		else:
			return time
	return None


def input_year(year_now):
	while True:
		year = input('Год (по умолчанию - текущий): ') or year_now
		if year == 'выход':
			return None
		try:
			if int(year) < year_now:
				raise ValueError
		except ValueError:
			print(f'Введите число больше {year_now}')
			continue
		return int(year)


def input_mounth(month_now):
	while True:
		month = input('Месяц (по умолчанию - текущий): ') or month_now
		if month == 'выход':
			return None
		try:
			if int(month) < month_now or int(month) > 12:
				raise ValueError
		except ValueError:
			print(f'Введите корректный месяц.')
			continue
		return int(month)


def input_day(year, month, day_now):
	while True:
		day = input('День (по умолчанию - текущий): ') or day_now
		if day == 'выход':
			return None
		try:
			if int(day) not in range(day_now, calendar.monthrange(year, month)[1]):
				raise ValueError
		except ValueError:
			print(f'Введите корректное число месяца.')
			continue
		return int(day)


def input_hour(default):
	while True:
		hour = input(f'Час (по умолчанию - {default}): ') or default
		if hour == 'выход':
			return None
		try:
			if int(hour) not in range(0, 24):
				raise ValueError
		except ValueError:
			print(f'Введите корректный час (0 - 23).')
			continue
		return int(hour)


def input_minute(default):
	while True:
		minute = input(f'Минута (по умолчанию - {default}): ') or default
		if minute == 'выход':
			return None
		try:
			if int(minute) not in range(0, 60):
				raise ValueError
		except ValueError:
			print(f'Введите корректное значение минут (0 - 59).')
			continue
		return int(minute)


def input_seconds(default):
	while True:
		second = input(f'Секунда (по умолчанию - {default}): ') or default
		if second == 'выход':
			return None
		try:
			if int(second) not in range(0, 60):
				raise ValueError
		except ValueError:
			print(f'Введите корректное значение секунд (0 - 59).')
			continue
		return int(second)


def format_delay_time(text):
	delay_for = re.findall(r'^([0-9]*):?([0-9]*):?([0-9]*)$', text)
	if delay_for:
		delay_for = list(delay_for[0])
		for i, t in enumerate(delay_for):
			if t != '':
				try:
					delay_for[i] = int(t)
				except ValueError:
					print('Неправильный формат ввода')
					return None
			else:
				delay_for[i] = 0
		delta = datetime.timedelta(
			hours=delay_for[0],
			minutes=delay_for[1],
			seconds=delay_for[2]		
		)
		today = datetime.datetime.now()
		return today + delta
	return None
