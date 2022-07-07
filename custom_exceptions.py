"""Кастомные исключения."""


class NotForSend(Exception):
    """Основной класс для кастомных исключений."""

    pass


class ConnectionError(Exception):
    """Выдает ошибку при запросе к основному API."""

    pass


class WrongResponseFromAPI(Exception):
    """Выбрасываем кастомное исключение НеВерныйОтветОтАПИ."""

    pass


class EmptyResponseFromAPI(NotForSend):
    """Проверяем что домашки или даты нет в респонсе."""

    pass


class TelegramError(NotForSend):
    """Проверка отправки сообщений в телеграм."""

    pass
