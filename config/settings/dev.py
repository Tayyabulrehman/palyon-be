from .base import *

# import os

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = os.getenv('SECRET_KEY')
SECRET_KEY = "3tcuyDqx8FpGeATiycLxsfTS8lhyGpXoYQV062mWi2EvawwDYJX2JNgTWxggnLl7eNQB4CEFbkicmVHZ7aBi8J3Xv89BBriC"
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']

# Temporary allowing CORS.
# CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_ALLOW_ALL = True
# CORS_ORIGIN_WHITELIST = ['http://192.168.18.41:3001']
# Database
# DATABASES['default'] =  dj_database_url.config()
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'enoteca_dev_db',
#         'USER': os.getenv('PG_USER'),
#         'PASSWORD': os.getenv('PG_PASSWD', ),
#         'HOST': os.getenv('PG_HOST', 'localhost'),
#         'PORT': '5432',
#     },
#     'OPTIONS': {
#         'options': '-c statement_timeout=5000'
#     }
# }
#
# SUPER_ADMIN = ["superadmin@yopmail.com"]
#
# WEB_URL = ''
#
# LOGGING_DIR = os.path.join(BASE_DIR, 'logs')  # Set your desired logs directory
#
# if not os.path.exists(LOGGING_DIR):
#     os.makedirs(LOGGING_DIR)
#
# CELERY_BROKER_URL = "redis://localhost:6377"
# CELERY_RESULT_BACKEND = "redis://localhost:6377"
