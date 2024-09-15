import os
import requests
import logging
import time
import sys

from telebot import TeleBot
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
    encoding='utf-8'
)


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


def check_tokens():
    """Проверяет наличие всех необходимых токенов."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствуют обязательные переменные окружения!')
        return False
    return True


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Бот отправил сообщение: {message}')
    except Exception:
        logging.error('Сообщение не отправлено')


def get_api_answer(timestamp):
    """Делает запрос к API Практикума и возвращает ответ."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        response.raise_for_status()
        if response.status_code != 200:
            logging.error(f'Ошибка ответа API: {response.status_code}')
            raise RuntimeError(f'Ошибка ответа API: {response.status_code}')
        return response.json()
    except requests.RequestException as e:
        logging.error(f'Ошибка при запросе к API: {e}')
        raise RuntimeError('Ошибка запроса к API Яндекс.Практикума') from e
    except ValueError as e:
        logging.error(f'Некорректный JSON в ответе API: {e}')
        raise ValueError('Некорректный формат ответа API (не JSON)') from e


def check_response(response):
    """Проверяет корректность ответа от API."""
    if type(response) is not dict:
        logging.error('API данные не соответсвуют типу данных')
        raise TypeError
    if type(response.get('homeworks')) is not list:
        logging.error('API данные не соответсвуют типу данных')
        raise TypeError
    return response.get('homeworks')


def parse_status(homework):
    """Формирует сообщение о статусе домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError('Отстутсвует ключ в ответе от API')
    if 'status' not in homework:
        raise KeyError('Отстутсвует ключ в ответе от API')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Ошибка "{homework_status}" в ответе API.')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = 1709280816

    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения!')
        sys.exit(1)

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Нет проверенных заданий'
            send_message(bot, message)

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
