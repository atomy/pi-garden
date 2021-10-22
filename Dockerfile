FROM python:3.9-alpine3.14

ADD emitter.py /opt/

RUN apk add --update py-pip build-base

RUN pip install asyncio-nats-client
RUN pip install Adafruit_DHT

WORKDIR "/opt"
CMD ["/usr/local/bin/python3", "emitter.py"]
