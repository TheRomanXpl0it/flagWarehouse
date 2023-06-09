DOCKER_COMPOSE = sudo docker compose

all: up

build: clear up

clear:
	rm -rf instance/flagWarehouse*

up:
	$(DOCKER_COMPOSE) up --build

down:
	$(DOCKER_COMPOSE) down

start:
	$(DOCKER_COMPOSE) start

stop:
	$(DOCKER_COMPOSE) stop


.PHONY: all up down start stop
