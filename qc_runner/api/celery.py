from celery import Celery
import api.config
from api.s3 import s3_init

app = Celery(__name__,
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0',
             include=['api.ftms_qc_tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

app.config_from_object('api.config')
s3 = s3_init()

if __name__ == '__main__':
    app.start()
