"""Кастомные исключения."""

import logging


class NotForSend(Exception):
    """Основной класс для кастомных исключений."""

    pass


class ConnectionError(NotForSend):
    """Выдает ошибку при запросе к основному API."""

    pass
    logging.error('Ошибка при запросе к основному API')


class WrongResponseFromAPI(NotForSend):
    """Выбрасываем кастомное исключение НеВерныйОтветОтАПИ."""

    pass
    logging.error('Ответа от API нет')


class EmptyResponseFromAPI(NotForSend):
    """Проверяем что домашки или даты нет в респонсе."""

    pass
    logging.error('Работы отсутствуют')
