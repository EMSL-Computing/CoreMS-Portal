app_name = corems-flask-app
workflow_app.endpoint = localhost:5000/gcms/remote-start-workflow
workflow_metadata = @tmp/MetamsFile.json
SQLALCHEMY_DATABASE_URI = postgresql+psycopg2://coremsappdb:coremsapppnnl@plocalhost:5432/coremsapp
version := $(shell cat ../.bumpversion.cfg | grep current_version | cut -d= -f2 | tr -d ' ')
stage := $(shell cat ../.bumpversion.cfg | grep optional_value | cut -d= -f2 | tr -d ' ') 

build:

	@docker build -t $(app_name) .

run-local:

	$(shell export SQLALCHEMY_DATABASE_URI=$(SQLALCHEMY_DATABASE_URI))
	@venv/bin/flask run

run-local-windows:

	$env:COREMS_DATABASE_URL = 'postgresql+psycopg2://coremsappdb:coremsapppnnl@plocalhost:5432/coremsapp'
	@ .\venv\Scripts\flask.exe run

run:

	@docker run --rm -d -p 5000:5000  \
	-v ~/Desenvolvimento/corems-app.:/app.\
	$(app_name)
	
kill:

	@echo 'Killing container...' 
	@docker ps | grep $(app_name) | awk '{print $$1}' | xargs docker kill

remote-pipeline:

	@curl -X POST -H "Content-Type: application/json" --data $(workflow_metadata) $(workflow_app.endpoint)

init-database:

	@export SQLALCHEMY_DATABASE_URI=$(SQLALCHEMY_DATABASE_URI)
	@venv/bin/flask db init
	@venv/bin/flask db migrate -m "users table"
	@venv/bin/flask db upgrade

init-database-kube:
	
	@flask db init
	@flask db migrate -m "users table"
	@flask db upgrade

install-redis:
	
	$(shell curl -O http://download.redis.io/redis-stable.tar.gz)
	$(shell tar xvzf redis-stable.tar.gz)
	$(shell rm redis-stable.tar.gz)
	$(shell cd redis-stable)
	$(shell make)
	redis-stable/src/redis-server

run-redis:

	@docker run -d -p 6379:6379 redis
	
run-celery-worker:

	@venv/bin/celery worker -A app.celery_worker.celery --loglevel=info --concurrency=6

run-celery-flower:

	@venv/bin/celery -A app.celery_worker.celery flower --concurrency=6

build-image:

	@echo corilo/corems-web:$(version).$(stage)
	@docker build --no-cache -t corilo/corems-web:$(version) .
	@docker push corilo/corems-web:$(version)
	
	@docker image tag corilo/corems-web:$(version) corilo/corems-web:latest
	@docker push corilo/corems-web:latest

	@docker image tag corilo/corems-web:latest emslcomputing/corems-web:latest
	@docker push emslcomputing/corems-web:latest

	@docker image tag emslcomputing/corems-web:latest emslcomputing/corems-web:$(version)
	@docker push emslcomputing/corems-web:$(version)

	@docker image rm corilo/corems-web:$(version)
	@docker image rm emslcomputing/corems-web:$(version)
	@docker image rm emslcomputing/corems-web:latest
