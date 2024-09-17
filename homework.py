import os
import sys

import requests
import logging
import time

from telebot import TeleBot
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='logs.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    encoding='utf-8'
)
logger = logging.StreamHandler(__name__)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

HTTP_OK = 200

STATUS_CHANGED_MSG = (
    'Изменился статус проверки работы "{homework_name}". {verdict}'
)
INVALID_STATUS_MSG = 'Ошибка "{homework_status}" в ответе API.'

last_message = None


# Настройка логирования
def setup_logging():
    """Настройка логгера с записью в файл и выводом в консоль."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_format = (
        '%(asctime)s, %(levelname)s, %(name)s, %(funcName)s, line'
        '%(lineno)d, %(message)s'
    )
    formatter = logging.Formatter(log_format)
    # Создание обработчика для вывода в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    # Создание обработчика для записи логов в файл
    log_file = os.path.join(os.path.expanduser('~'), f'{__file__}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    # Добавляем оба обработчика в логгер
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def check_tokens(logger):
    """Проверяет наличие всех необходимых токенов и логгирует отсутствующие."""
    missing_tokens = []
    required_tokens = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    for name in required_tokens:
        if not globals().get(name):
            missing_tokens.append(name)
    if missing_tokens:
        logger.critical(f'Отсутствуют обязательные переменные окружения: '
                        f'{", ".join(missing_tokens)}'
                        )
        return False
    return True


def send_message(bot, message):
    """Отправляет сообщение, если оно не совпадает с последним отправленным."""
    global last_message
    if message != last_message:
        try:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            logger = logging.getLogger(__name__)
            logger.debug(f'Бот отправил сообщение: {message}')
            last_message = message  # Обновляем последнее сообщение
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f'Сообщение не отправлено: "{message}". Ошибка: {e}',
                         exc_info=True)
    return last_message  # Возвращаем без изменений, если сообщение не изм


def get_api_answer(timestamp):
    """Делает запрос к API Практикума и возвращает ответ."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTP_OK:
            raise RuntimeError(
                f'Ошибка ответа API: {response.status_code}, '
                f'параметры запроса: {params}, '
                f'тело ответа: {response.text}'
            )
        response_json = response.json()
        # Проверка на наличие ключей code или error в ответе
        if 'code' in response_json or 'error' in response_json:
            raise RuntimeError(
                f'Ошибка в ответе API: {response_json}, '
                f'параметры запроса: {params}'
            )
        return response_json
    except requests.RequestException as e:
        raise RuntimeError(
            f'Ошибка запроса к API Яндекс.Практикума: {e}, '
            f'параметры запроса: {params}'
        ) from e


def check_response(response):
    """Проверяет корректность ответа от API."""
    if not isinstance(response, dict):
        raise TypeError(f'Ожидался dict, но получен {type(response).__name__}')
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError('Отсутствует ключ "homeworks" в ответе API')
    if not isinstance(homeworks, list):
        raise TypeError(f'Ожидался list для ключа "homeworks", но получен '
                        f'{type(homeworks).__name__}')
    return homeworks


def parse_status(homework):
    """Формирует сообщение о статусе домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError(f'Ожидался dict, получен {type(homework).__name__}')
    homework_name = homework.get('homework_name')
    status = homework.get('status')

    if homework_name is None:
        raise KeyError('Отсутствует ключ "homework_name" в данных о домашке')
    if not isinstance(status, str):
        raise TypeError(f'Ожидался str, получен {type(status).__name__}')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(INVALID_STATUS_MSG.format(homework_status=status))
    verdict = HOMEWORK_VERDICTS[status]
    return STATUS_CHANGED_MSG.format(homework_name=homework_name,
                                     verdict=verdict)


def main():
    """Основная логика работы бота."""
    logger = setup_logging()

    if not check_tokens(logger):
        raise EnvironmentError('Отсутствуют обязательные переменные окружения')
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            # Обновляем timestamp на основе данных из ответа
            if 'current_date' in response:
                timestamp = response['current_date']
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                message = 'Нет новых статусов для проверки.'
                logger.debug(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message, exc_info=True)
            # Обновляем last_message и отправляем сообщение

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
