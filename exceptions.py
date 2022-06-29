"""Exceptions for homework."""

class EnvironmentVariableNotFoundError(Exception):
    def __str__(self):
        return f'Environment variable is not found! Program will be closed!'

class HomeworkStatusIsUndefinedError(Exception):
    def __str__(self):
        return f'Homework status is undefined!'

class HomeworkStatusDoesNotExistError(Exception):
    def __str__(self):
        return f'Homework status does not exist!'

class HomeworkNameDoesNotExistError(Exception):
    def __str__(self):
        return f'Homework name does not exist!'

class ApiAnswerIsNotOkError(Exception):
    def __str__(self):
        return f'API answer is not 200!'
