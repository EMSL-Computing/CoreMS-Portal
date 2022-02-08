FROM corilo/corems:base-mono-pythonnet

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

#COPY . /app
CMD gunicorn --reload --chdir app.app.app -w 2 --threads 2 -b 0.0.0.0:5000
CMD gunicorn -w 2 -b :8000 app:create_app()
CMD celery worker -A api.celery --loglevel=info --concurrency=6