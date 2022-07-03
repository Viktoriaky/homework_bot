import logging
import os

import time
from http import HTTPStatus
import requests
import telegram

from logging import StreamHandler

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('P_T')
TELEGRAM_TOKEN = os.getenv('T_T')
TELEGRAM_CHAT_ID = os.getenv('T_C_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    encoding='UTF-8'
)

handler = StreamHandler(stream='sys.stdout')


def send_message(bot, message):
    """Oтправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            message.chat.id,
            messsage='Привет! Ты только посмотри, что ревьюер написал!',
        )
        logging.info('Сообщене отправлено')
    except Exception:
        logging.error('Сообщение не отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )

    except Exception as error:
        raise Exception(f'Ошибка при запросе к основному API: {error}')

    if response.status_code != HTTPStatus.OK:
        status_code = response.status_code
        raise Exception(f'Ошибка доступа {status_code}')

    try:
        response_dict = response.json()
        return response_dict
    except ValueError:
        logging.error('Ошибка обработки json')
        raise ValueError('Ошибка обработки json')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Неверный тип данных')

    homework = response['homeworks']

    if not isinstance(homework, list):
        raise TypeError('Неверный тип данных')
    elif not homework:
        raise Exception('Работы отсутствуют')
    else:
        return response.get('homeworks')


def parse_status(homework):
    """Извлекаем статус работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ "homework_name" отсутствует')
    homework_name = homework['homework_name']

    if 'status' not in homework:
        raise KeyError('Ключ "status" отсутствует')

    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        raise ValueError('Отсутствуют в ответе новые статусы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов на доступность."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]) is False:
        logging.critical('Отсутствуют обязательные переменные окружения')
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    if not check_tokens():
        raise Exception('Токены не найдены')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homework = check_response(response)
            if homework:
                send_message(bot, parse_status(homework))

        except Exception as error:
            logging.exception(f'Что-то пошло совсем не так: {error}')
            bot.send_message(
                TELEGRAM_CHAT_ID,
                f'Что-то пошло совсем не так: {error}'
            )

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
