FROM python:3.8-slim-buster

WORKDIR /server

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 5000

CMD [ "bash", "run.sh"]