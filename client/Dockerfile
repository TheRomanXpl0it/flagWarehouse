FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && \
    apt install -y \
        python3 python-is-python3 python3-pip \
        curl wget nano git unzip
RUN pip install pwntools pycryptodome requests tqdm

RUN mkdir -p /flagWarehouse/client/
COPY . /flagWarehouse/client/
WORKDIR /flagWarehouse/client

CMD python ./client.py -s <URL> -u prod -t <API_TOKEN> -d exploits/ -n 64
