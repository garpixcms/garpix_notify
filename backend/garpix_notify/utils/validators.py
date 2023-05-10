
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
)


def validate_file_extension(value, allowed_extensions):
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)


def validate_zip(value):
    allowed_extensions = ['zip', 'rar']
    validate_file_extension(value, allowed_extensions)
    filesize = value.file.size
    megabyte_limit = 100.0
    if filesize > megabyte_limit * 1024 * 1024:
        raise ValidationError("Максимальный допустимый размер изображения %sMB" % str(megabyte_limit))


def validate_zip_files(value):
    allowed_extensions = ['png', 'jpg', 'jpeg', 'html']
    validate_file_extension(value, allowed_extensions)
