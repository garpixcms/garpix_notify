import datetime
import uuslug


def get_file_path(instance, filename):
    """
    Формирует путь файла относительно года и месяца, чтобы множество файлов не скапливались на одном уровне.
    """
    ext = filename.split('.')[-1]
    today = datetime.date.today()
    filename = f'{uuslug.slugify(".".join(filename.split(".")[:-1]))}.{ext}'
    return f'uploads/{today.year}/{today.month}/{filename}'
