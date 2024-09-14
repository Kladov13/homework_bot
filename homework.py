import os
import requests
import logging
import time

from telebot import TeleBot, types
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

last_status = None

def check_tokens():
    if not (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        return False
    return True


def send_message(bot, message):
    global last_status
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('/status')
    keyboard.add(button)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message,
                         reply_markup=keyboard)
        last_status = message
        logging.debug(f'Бот отправил сообщение: {message}')
    except:
        logging.error(f'Сообщение не отправлено')





def get_api_answer(timestamp):
    params = {'from_date': timestamp}
    return requests.get(ENDPOINT, headers=HEADERS,
                        params=params).json()


def check_response(response):
    return response.get('homeworks')


def parse_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_VERDICTS[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""


    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = 1709280816

    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения!')
        return
   
    @bot.message_handler(commands=['status'])
    def handle_status(message):
        bot.reply_to(message, last_status)

    

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
