from datetime import timedelta
import os

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or '9OLWxND4o83j4K4iuopO'
    UPLOAD_FOLDER = f"{os.getenv('APP_FOLDER')}/app/data"

    directory = os.getcwd()

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SESSION_TYPE = os.environ.get('SESSION_TYPE') or 'memcached'

    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

    COREMS_DATABASE_URL = os.getenv("COREMS_DATABASE_URL", "sqlite:///db/molformulas.sqlite")
    COREMS_API_URL = os.getenv("COREMS_API_URL", "http://localhost:5000")
    INSTRUMENT_API_URL = os.getenv("INSTRUMENT_API_URL", "http://localhost:3443")

    SPECTRAL_GCMS_DATABASE_URL = os.getenv("SPECTRAL_GCMS_DATABASE_URL", "sqlite:///db/molformulas.sqlite")

    RECAPTCHA_USE_SSL = os.getenv("RECAPTCHA_USE_SSL", False)
    RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_USE_SSL", 'public')
    RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_USE_SSL", 'private')
    RECAPTCHA_OPTIONS = os.getenv("RECAPTCHA_USE_SSL", {'theme': 'white'})

    REMEMBER_COOKIE_DURATION = timedelta(hours=12)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    # MAX_CONTENT_LENGTH = os.environ.get('MAX_CONTENT_LENGTH') or '128 * 1024 * 1024'
