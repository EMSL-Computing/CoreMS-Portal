version := $(shell cat ../.bumpversion.cfg | grep current_version | cut -d= -f2 | tr -d ' ')
stage := $(shell cat ../.bumpversion.cfg | grep optional_value | cut -d= -f2 | tr -d ' ') 

run-worker:
	
	@venv/bin/celery worker -A api.celery --loglevel=info --concurrency=6

run-celery-flower:
	
	@venv/bin/celery -A api.celery --concurrency=6 flower

build-image:

	@echo corilo/corems-runner:$(version).$(stage)
	@docker build --no-cache -t corilo/corems-runner:$(version) .
	@docker push corilo/corems-runner:$(version)
	@docker image tag corilo/corems-runner:$(version) corilo/corems-runner:latest
	@docker push corilo/corems-runner:latest

	@docker image tag corilo/corems-runner:latest emslcomputing/corems-runner:latest
	@docker push emslcomputing/corems-runner:latest

	@docker image tag emslcomputing/corems-runner:latest emslcomputing/corems-runner:$(version)
	@docker push emslcomputing/corems-runner:$(version)

	@docker image rm corilo/corems-runner:$(version)
	@docker image rm emslcomputing/corems-runner:$(version)
	@docker image rm emslcomputing/corems-runner:latest