import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
#
# TEMPLATE_DIRS = [
#     os.path.join(BASE_DIR, 'tests_django'),
#     os.path.join(BASE_DIR, 'tri/form/templates'),
# ]

TEMPLATE_DEBUG = True

SECRET_KEY = "foobar"
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tri.form',
    'tests_django',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
