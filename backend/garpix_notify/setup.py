from setuptools import setup, find_packages
from os import path

here = path.join(path.abspath(path.dirname(__file__)), 'garpix_notify')

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='garpix_notify',
    version='5.11.5',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/garpixcms/garpix_notify',
    author='Garpix LTD',
    author_email='info@garpix.com',
    license='MIT',
    packages=find_packages(exclude=['testproject', 'testproject.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Django >= 1.11',
        'django-solo >= 1.1.3',
        'fcm-django == 0.3.11',
        'requests >= 2.18.4',
        'django-ckeditor >= 5.6.1',
        'python-telegram-bot >= 12.6.1',
        'viberbot >= 1.0.11',
        'django-uuslug >= 1.2.0',
        'Pillow >= 8.2.0',
        'celery>=4.4.2',
        'redis >= 3.5.3',
        'channels >= 3.0.3, <= 3.0.4',
        'channels-redis == 3.4.0',
        'asgiref >= 3.2.10, <= 3.3.4',
        'twilio == 7.10.0',
        'typing-extensions >= 4.3.0'
    ],
)
