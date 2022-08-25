class ArgumentsEmptyException(Exception):
    message = 'You must pass one of the "user" or "event" or "templates" arguments'

    def __init__(self):
        super().__init__(self.message)


class DataTypeException(Exception):

    def __init__(self, field, data_type):
        self.field = field
        self.data_type = data_type
        message = f'The data type error: "{self.field}" type is not {self.data_type}'
        super().__init__(message)


class IsInstanceException(Exception):
    message = 'The "user" argument must be a "User" instance'

    def __init__(self):
        super().__init__(self.message)


class TemplatesNotExists(Exception):
    message = 'NotifyTemplates not exists'

    def __init__(self):
        super().__init__(self.message)


class UsersListIsNone(Exception):
    message = 'The list of users is empty'

    def __init__(self):
        super().__init__(self.message)
