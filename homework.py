import os
import sys
import time
import logging

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (EnvironmentVariableNotFoundError,
                        ApiAnswerIsNotOkError,
                        HomeworkNameDoesNotExistError,
                        HomeworkStatusDoesNotExistError,
                        HomeworkStatusIsUndefinedError)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Send message to telegram chat."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Make request to API`s endpoint. If success returns API response."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    homework_statuses = requests.get(ENDPOINT, headers=headers, params=params)
    if homework_statuses.status_code != 200:
        raise ApiAnswerIsNotOkError()
    return homework_statuses.json()


def check_response(response):
    """Check API response for it`s validity.
    If API response is valid return list of homeworks even empty.
    """
    if not isinstance(response, dict):
        raise TypeError('Response must be dictionary!')
    if len(response) == 0:
        raise ValueError('Response must not be empty!')
    homework = response['homeworks']
    if type(homework) != list:
        raise TypeError('Homeworks must be in a list!')
    return homework


def parse_status(homework):
    """Extract from information about concrete homework it`s status.
    If extraction was successful, return string with homework verdict.
    """
    if not homework['homework_name']:
        raise HomeworkNameDoesNotExistError
    homework_name = homework['homework_name']
    if not homework['status']:
        raise HomeworkStatusDoesNotExistError()
    if homework['status'] not in HOMEWORK_STATUSES.keys():
        raise HomeworkStatusIsUndefinedError()
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check existing of environmental tokens.
    If some of them does not exist return False, else True.
    """
    return all((PRACTICUM_TOKEN,
                TELEGRAM_TOKEN,
                TELEGRAM_CHAT_ID))


def main():
    """Main bot logic."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    logger = logging.getLogger(__name__)
    logger.addHandler(sys.stdout)

    try:
        check_tokens()
        logging.info('All tokens are available!')
    except EnvironmentVariableNotFoundError() as exc:
        logging.critical(exc)
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.info('Response has been successfully required!')
            current_timestamp = int(time.time())
            homeworks = check_response(response)
            logging.info('Response has been successfully checked!')
            for homework in homeworks:
                send_message(bot, parse_status(homework))
                logging.info('Homework status is changed!')

            time.sleep(RETRY_TIME)
        except (ApiAnswerIsNotOkError, TypeError, ValueError,
                HomeworkNameDoesNotExistError,
                HomeworkStatusDoesNotExistError,
                HomeworkStatusIsUndefinedError,
                KeyError) as error:
            logging.error(error)
            send_message(bot, error)
        except Exception as error:
            logging.error(error)
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.info(f'Message {message} was sent.')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
