"""Exceptions for homework."""


class OnlyForLogError(Exception):
    pass

class MessageHasNotSentError(OnlyForLogError):
    def __str__(self):
        return f'Message has not sent'

class WrongStatusCodeError(Exception):
    def __str__(self):
        return f'Status code is not 200!'

class JSONDecodeProblemError(Exception):
    def __str__(self):
        return f'Response contains invalid JSON or contains no content'

class ResponseCurrentDateNotFoundError(OnlyForLogError):
    def __str__(self):
        return f'Key "current_date" is not found in response!'
