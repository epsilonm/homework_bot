import os
import sys
import time
import logging
import http

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (ApiAnswerIsNotOkError,
                        HomeworkStatusIsUndefinedError,
                        MessageHasNotSentError)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ENV_VARS = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
            'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
            'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
            }

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

RESPONSE_KEYS = ('homeworks', 'current_date',)

HOMEWORK_KEYS = ('id', 'status', 'homework_name', 'reviewer_comment',
                 'date_updated', 'lesson_name',)


def send_message(bot, message):
    """Send message to telegram chat."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Message {message} was sent.')
    except MessageHasNotSentError:
        raise MessageHasNotSentError(f'{message}')


def get_api_answer(current_timestamp):
    """Make request to API`s endpoint. If success returns API response."""
    request_parameters = {
        'params': {'from_date': current_timestamp},
        'url': ENDPOINT,
        'headers': {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    }
    try:
        homeworks = requests.get(**request_parameters)
    except ConnectionError:
        raise ConnectionError
    if homeworks.status_code != http.HTTPStatus.OK:
        raise requests.exceptions.HTTPError(
            f'API is not available, status code: '
            f'{homeworks.status_code}, '
            f'{homeworks.reason},'
        )
    try:
        homeworks = homeworks.json()
    except requests.exceptions.InvalidJSONError:
        raise requests.exceptions.InvalidJSONError(
            'Response contains invalid JSON'
        )
    logging.info('Response has been successfully required!')
    return homeworks


def check_response(response):
    """Check API response for it`s validity.
    If API response is valid return list of homeworks even empty.
    """
    if not isinstance(response, dict):
        raise TypeError('Response must be dictionary!')
    for key in RESPONSE_KEYS:
        if key not in response.keys():
            raise KeyError(f'Key {key} is not found.')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks must be in a list!')
    logging.info('Response has been successfully checked!')
    return homeworks


def parse_status(homework):
    """Extract from information about concrete homework it`s status.
    If extraction was successful, return string with homework verdict.
    """
    for key in HOMEWORK_KEYS:
        if homework.get(key) is None:
            raise KeyError(f'Key {key} is not found.')
    homework_name = homework['homework_name']
    if homework['status'] not in HOMEWORK_STATUSES.keys():
        raise HomeworkStatusIsUndefinedError()
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check existing of environmental tokens.
    If some of them does not exist return False, else True.
    """
    return all(ENV_VARS.values())


def main():
    """Main bot logic."""
    logger = logging.getLogger(__name__)

    if check_tokens():
        logger.debug('All tokens are available!')
    else:
        missing = [key for key, value in ENV_VARS.items() if value is None]
        logger.critical(f'Environment variable is not found! '
                        f'Program will be closed! '
                        f'Missing variables: {missing}')
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date']
            homeworks = check_response(response)
            if len(homeworks) != 0:
                send_message(bot, parse_status(homeworks[0]))
                logger.info('Homework status is changed!')
            else:
                logger.info('Homework status was not changed!')

        except (ApiAnswerIsNotOkError, TypeError, ValueError,
                HomeworkStatusIsUndefinedError,
                KeyError,
                ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.InvalidJSONError,
                ) as error:
            logger.exception(error)
            message = f'Program failure: {error}'
            send_message(bot, message)
        except Exception as error:
            logger.exception(error)
            message = f'Unexpected program failure: {error}'
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s, %(levelname)s, '
                ' %(message)s, '
                'in function: %(funcName)s, '
                'line: %(lineno)d'),
        handlers=(logging.StreamHandler(stream=sys.stdout),)
    )
    main()
