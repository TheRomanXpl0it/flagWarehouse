DC = sudo docker compose

all: up

build:
	$(DC) up --build

clear:
	rm -rf instance/flagWarehouse*

up:
	$(DC) up

down:
	$(DC) down

start:
	$(DC) start

stop:
	$(DC) stop


.PHONY: all up down start stop
