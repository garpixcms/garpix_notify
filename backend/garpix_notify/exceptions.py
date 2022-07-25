class ArgumentsEmptyException(Exception):
    message = 'You must pass one of the "user" or "event" arguments'

    def __init__(self):
        super().__init__(self.message)


class DataTypeException(Exception):

    def __init__(self, field):
        self.field = field
        message = f'The data type error: "{self.field}" type is not dict'
        super().__init__(message)


class IsInstanceException(Exception):
    message = 'The "user" argument must be a "User" instance'

    def __init__(self):
        super().__init__(self.message)


class TemplatesNotExists(Exception):
    message = 'NotifyTemplates not exists'

    def __init__(self):
        super().__init__(self.message)
