import os


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')

REQUIRED_TOKENS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
MISSING_TOKENS = 'Отсутствуют обязательные переменные окружения: {}'

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

SEND_MESSAGE_DEBUG = 'Бот отправил сообщение: {}'
SEND_MESSAGE_ERROR = 'Сообщение не отправлено: "{}". Ошибка: {}'

STATUS_CHANGED = (
    'Изменился статус проверки работы "{homework_name}". {verdict}'
)
INVALID_STATUS = 'Ошибка "{homework_status}" в ответе API.'

ERROR_API_RESPONSE = (
    'Ошибка ответа API: {status_code}, '
    'параметры запроса: {params}'
)
ERROR_API_JSON = (
    'Ошибка в ответе API: {response_json}, '
    'параметры запроса: {params}'
)
ERROR_REQUEST = (
    'Ошибка запроса к API Яндекс.Практикума: {error}, '
    'параметры запроса: {params}'
)

ERROR_MISSING_HOMEWORKS_KEY = 'Отсутствует ключ "homeworks" в ответе API'

EXPECTED_TYPE = 'Ожидался dict, но получен {type_name}'
EXPECTED_LIST = 'Ожидался list для ключа "{key}", но получен {type_name}'


NEW_STATUSES = 'Нет новых статусов для проверки.'

ERROR_FAILURE = 'Сбой в работе программы: {error}'
