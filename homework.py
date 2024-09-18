import os
import sys
import logging
import time
from http import HTTPStatus

import requests
from telebot import TeleBot
from dotenv import load_dotenv

from constants import (
    ERROR_KEY_VALUE,
    REQUIRED_TOKENS,
    MISSING_TOKENS,
    RETRY_PERIOD,
    ENDPOINT,
    HEADERS,
    HOMEWORK_VERDICTS,
    SEND_MESSAGE_DEBUG,
    SEND_MESSAGE_ERROR,
    STATUS_CHANGED,
    INVALID_STATUS,
    ERROR_API_RESPONSE,
    ERROR_API_JSON,
    EXPECTED_LIST,
    ERROR_MISSING_HOMEWORKS_KEY,
    EXPECTED_TYPE,
    NEW_STATUSES,
    ERROR_FAILURE
)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logger = logging.getLogger(__name__)


def check_tokens(logger):
    """Проверяет наличие всех необходимых токенов и логгирует отсутствующие."""
    missing_tokens = [
        name for name in REQUIRED_TOKENS
        if not globals().get(name)
    ]
    if missing_tokens:
        logger.critical(MISSING_TOKENS.format(missing_tokens))
        raise EnvironmentError(MISSING_TOKENS.format(missing_tokens))


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(SEND_MESSAGE_DEBUG.format(message))
    except Exception as e:
        logger.error(SEND_MESSAGE_ERROR.format(message, e), exc_info=True)


def get_api_answer(timestamp):
    """Делает запрос к API Практикума и возвращает ответ."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    except requests.RequestException as e:
        raise ConnectionError(
            error=e,
            params=params
        ) from e
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(
            ERROR_API_RESPONSE.format(
                status_code=response.status_code,
                params=params
            )
        )
    response_json = response.json()
    # Проверка на наличие ключей code или error в ответе
    if 'code' in response_json or 'error' in response_json:
        error_key = 'code' if 'code' in response_json else 'error'
        error_value = response_json.get(error_key)
        raise RuntimeError(
            ERROR_API_JSON.format(
                response_json=ERROR_KEY_VALUE.format(key=error_key,
                                                     value=error_value),
                params=params
            )
        )
    return response_json


def check_response(response):
    """Проверяет корректность ответа от API."""
    if not isinstance(response, dict):
        raise TypeError(
            EXPECTED_TYPE.format(type_name=type(response).__name__)
        )
    if 'homeworks' not in response:
        raise KeyError(ERROR_MISSING_HOMEWORKS_KEY)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            EXPECTED_LIST.format(
                key='homeworks',
                type_name=type(homeworks).__name__
            )
        )
    return homeworks


def parse_status(homework):
    """Формирует сообщение о статусе домашней работы."""
    if 'homework_name' not in homework:
        error_message = ERROR_MISSING_HOMEWORKS_KEY.format(key='homework_name')
        raise KeyError(error_message)
    homework_name = homework['homework_name']
    if 'status' not in homework:
        error_message = ERROR_MISSING_HOMEWORKS_KEY.format(key='status')
        raise KeyError(error_message)
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(INVALID_STATUS.format(homework_status=status))
    verdict = HOMEWORK_VERDICTS[status]
    return STATUS_CHANGED.format(homework_name=homework_name, verdict=verdict)


def main():
    """Основная логика работы бота."""
    logger = logging.getLogger(__name__)
    check_tokens(logger)
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message = None
    while True:
        message_sent = False
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
                message_sent = True
            else:
                logger.debug(NEW_STATUSES)
        except Exception as error:
            message = ERROR_FAILURE.format(error=error)
            logger.error(message, exc_info=True)
            if message != last_error_message:
                send_message(bot, message)
            if message_sent:
                timestamp = response.get('current_date', timestamp)
                last_error_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':

    log_file = os.path.join(os.path.expanduser('~'), f'{__file__}.log')
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s, %(levelname)s, %(name)s, %(funcName)s,'
                'line %(lineno)d, %(message)s'),
        handlers=[
            logging.StreamHandler(sys.stdout),  # Вывод в консоль
            logging.FileHandler(log_file, encoding='utf-8')  # Логи в файл
        ]
    )
    main()
