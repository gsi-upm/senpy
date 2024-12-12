from .models import ErrorResponse

class Error(Exception):
    def __init__(self, message='Generic senpy exception', errors=[]):
        Exception.__init__(self, message)
        self.message = message
        self.errors = errors

    def toResponse(self) -> ErrorResponse:
        return ErrorResponse(self.message)

    def __str__(self):
        if not hasattr(self, 'errors'):
            return self.message
        return '{}:\n\t{}'.format(self.message, self.errors)

    def __hash__(self):
        return Exception.__hash__(self)


class InvalidParams(Error):
    def __init__(self, wrong_params):
        super().__init__(message='Wrong parameters:\n\t{}'.format(wrong_params))
