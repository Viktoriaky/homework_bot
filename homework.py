import logging
import os
import sys
import time

import requests
import telegram

import custom_exceptions

from http import HTTPStatus

from dotenv import load_dotenv


load_dotenv()


PRACTICUM_TOKEN = os.getenv('P_T')
TELEGRAM_TOKEN = os.getenv('T_T')
TELEGRAM_CHAT_ID = os.getenv('T_C_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Oтправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.info('Начался процесс отправки сообщения')
    except custom_exceptions.TelegramError as error:
        raise custom_exceptions.TelegramError(
            f'Сообщение не отправлено {error}')
    else:
        logging.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_dict = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params,
    }
    try:
        logging.info(
            'Отправляем запрос: url={url},'
            'headers={headers},'
            'params={params}'.format(**homework_dict)
        )
        response = requests.get(**homework_dict)

        if response.status_code != HTTPStatus.OK:

            raise custom_exceptions.WrongResponseFromAPI(
                'Ошибка доступа: url = {url},'
                'headers = {headers},'
                'params = {params}'.format(**homework_dict)
            )
        return response.json()

    except Exception:
        raise custom_exceptions.ConnectionError(
            'Нет ответа API,'
            f'ошибка: {response.status_code}'
            f'причина: {response.reason}'
            f'текст: {response.text}'
        )


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.info('Начинаем проверку на корректность API')
    if not isinstance(response, dict):
        raise TypeError('Неверный тип данных')
    if 'homeworks' not in response or 'current_date' not in response:
        raise custom_exceptions.EmptyResponseFromAPI()

    homework = response.get('homeworks')

    if not isinstance(homework, list):
        raise KeyError('Неверный тип данных')

    return homework


def parse_status(homework):
    """Извлекаем статус работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ "homework_name" отсутствует')
    homework_name = homework.get('homework_name')

    if 'status' not in homework:
        raise KeyError('Ключ "status" отсутствует')

    homework_status = homework.get('status')

    if homework_status not in VERDICTS:
        raise ValueError('Отсутствуют в ответе новые статусы')
    return ('Изменился статус проверки работы'
            ' "{homework_name}"{verdict}').format(
                homework_name=homework_name,
                verdict=VERDICTS[homework_status])


def check_tokens():
    """Проверка токенов на доступность."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Токен(ы) не найдены')
        sys.exit('Токен(ы) не найдены')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    current_report = {
        'name': '',
        'messages': '',
    }
    prev_report = {
        'name': '',
        'messages': '',
    }

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            homework = check_response(response)

            if homework:
                homework_new = homework[0]
                current_report['name'] = homework_new.get('homework_name')
                current_report['messages'] = homework_new.get('status')
            else:
                current_report['messages'] = 'Нет новых статусов'

            if current_report != prev_report:
                message = f'{current_report["name"]},'
                f'{current_report["messages"]}'
                send_message(bot, message)
                prev_report = current_report.copy()
            else:
                logging.info('Новых статусов нет')

        except custom_exceptions.NotForSend as error:
            logging.error({error})
        except Exception as error:
            logging.exception(f'Что-то пошло совсем не так: {error}')
            current_report['messages'] = 'Что-то не так: {error}'
            current_report != prev_report
            send_message(
                bot,
                f'{current_report["messages"]}'
            )
            prev_report = current_report.copy()

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)d',
        handlers=[logging.StreamHandler(stream='sys.stdout'),
                  logging.FileHandler(
                  os.path.join(BASE_DIR, 'bot.log'), encoding='UTF-8')],
    )
    main()
