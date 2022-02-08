
import os

broker_url = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
result_backend = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

task_track_started = True
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'US/Pacific'
enable_utc = True
