version := $(shell cat .bumpversion.cfg | grep current_version | cut -d= -f2 | tr -d ' ')
stage := $(shell cat .bumpversion.cfg | grep optional_value | cut -d= -f2 | tr -d ' ') 

all-up:

	@docker-compose up -d --build
	@docker-compose exec web flask db init
	@docker-compose exec web flask db migrate -m "users table"
	@docker-compose exec web flask db upgrade

db-init:
	@docker-compose exec web flask db init
	@docker-compose exec web flask db migrate -m "users table"
	@docker-compose exec web flask db upgrade
	
celery-worker:
	@docker-compose exec web celery -A app.celery_worker.celery worker --loglevel=INFO --concurrency=6

kube-direct:
	@kompose up -f docker-compose.yml

kubectl-deploy:
	@kompose convert -f docker-compose.yml -o ./kubernetes
	@kubectl create -f ./kubernetes

major:
	
	@bumpversion major --allow-dirty

minor:
	
	@bumpversion minor --allow-dirty

patch:
	
	@bumpversion patch --allow-dirty

push-runner-image:

	@echo corems-app_runner:$(version)
	
	@docker image tag corems-app_runner:latest corilo/corems-runner:$(version)
	@docker push corilo/corems-runner:$(version)

	@docker image tag corems-app_runner:latest corilo/corems-runner:latest
	@docker push corilo/corems-runner:latest

	@docker image tag corilo/corems-runner:latest emslcomputing/corems-runner:latest
	@docker push emslcomputing/corems-runner:latest

	@docker image tag emslcomputing/corems-runner:latest emslcomputing/corems-runner:$(version)
	@docker push emslcomputing/corems-runner:$(version)

	@docker image rm corilo/corems-runner:$(version)
	@docker image rm emslcomputing/corems-runner:$(version)
	@docker image rm emslcomputing/corems-runner:latest


push-web-image:

	@echo corems-app_web:$(version)
	
	@docker image tag corems-app_web:latest corilo/corems-web:$(version)
	@docker push corilo/corems-web:$(version)

	@docker image tag corems-app_web:latest corilo/corems-web:latest
	@docker push corilo/corems-web:latest

	@docker image tag corilo/corems-web:latest emslcomputing/corems-web:latest
	@docker push emslcomputing/corems-web:latest

	@docker image tag emslcomputing/corems-web:latest emslcomputing/corems-web:$(version)
	@docker push emslcomputing/corems-web:$(version)

	@docker image rm corilo/corems-web:$(version)
	@docker image rm emslcomputing/corems-web:$(version)
	@docker image rm emslcomputing/corems-web:latest

push-all-images:

	@echo corems-app_web:$(version)
	
	@docker image tag corems-app_web:latest corilo/corems-web:$(version)
	@docker push corilo/corems-web:$(version)

	@docker image tag corems-app_web:latest corilo/corems-web:latest
	@docker push corilo/corems-web:latest

	@docker image tag corilo/corems-web:latest emslcomputing/corems-web:latest
	@docker push emslcomputing/corems-web:latest

	@docker image tag emslcomputing/corems-web:latest emslcomputing/corems-web:$(version)
	@docker push emslcomputing/corems-web:$(version)

	@docker image rm corilo/corems-web:$(version)
	@docker image rm emslcomputing/corems-web:$(version)
	@docker image rm emslcomputing/corems-web:latest

	@echo corems-app_runner:$(version)
	
	@docker image tag corems-app_runner:latest corilo/corems-runner:$(version)
	@docker push corilo/corems-runner:$(version)

	@docker image tag corems-app_runner:latest corilo/corems-runner:latest
	@docker push corilo/corems-runner:latest

	@docker image tag corilo/corems-runner:latest emslcomputing/corems-runner:latest
	@docker push emslcomputing/corems-runner:latest

	@docker image tag emslcomputing/corems-runner:latest emslcomputing/corems-runner:$(version)
	@docker push emslcomputing/corems-runner:$(version)

	@docker image rm corilo/corems-runner:$(version)
	@docker image rm emslcomputing/corems-runner:$(version)
	@docker image rm emslcomputing/corems-runner:latest
