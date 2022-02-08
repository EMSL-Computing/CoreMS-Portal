import os

broker_url = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
result_backend = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'US/Pacific'
enable_utc = True
task_track_started = True

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://coremsappdb:coremsapppnnl@localhost:5432/coremsapp'
SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS') or False
COREMS_DATABASE_URL = os.getenv("COREMS_DATABASE_URL", "sqlite:///db/molformulas.sqlite")
SPECTRAL_GCMS_DATABASE_URL = os.getenv("SPECTRAL_GCMS_DATABASE_URL", "sqlite:////usr/src/corems-runner/db/pnnl_lowres_gcms_compounds.sqlite")

MINIO_URL = os.environ.get("MINIO_URL", 'http://localhost:9000')
MINIO_ROOT_USER = os.environ.get("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.environ.get("MINIO_ROOT_PASSWORD")