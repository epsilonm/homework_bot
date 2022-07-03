"""Exceptions for homework."""


class HomeworkStatusIsUndefinedError(Exception):
    def __str__(self):
        return f'Homework status is undefined!'

class ApiAnswerIsNotOkError(Exception):
    def __str__(self):
        return f'API answer is not 200!'

class MessageHasNotSentError(Exception):
    def __str__(self):
        return f'Message has not sent'