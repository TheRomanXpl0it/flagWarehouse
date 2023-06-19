DC = sudo docker compose

all: up

build:
	$(DC) up --build --no-log-prefix

clear:
	rm -rf instance/flagWarehouse*

up:
	$(DC) up --no-log-prefix

down:
	$(DC) down

start:
	$(DC) start

stop:
	$(DC) stop


.PHONY: all up down start stop
