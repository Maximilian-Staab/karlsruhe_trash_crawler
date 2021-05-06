all: build deploy

build:
	docker build -t trash-python . -f Dockerfile

deploy: build
	docker image tag trash-python 192.168.0.207:5000/trash-python
	docker push 192.168.0.207:5000/trash-python

update: deploy
	ssh nextcloud "cd trash-dates && docker-compose pull && docker-compose up -d"
