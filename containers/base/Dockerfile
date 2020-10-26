FROM python:3.8-alpine3.12

RUN apk update
RUN apk --no-cache add make automake gcc g++ linux-headers curl libcurl curl-dev \
  zlib-dev bzip2-dev xz-dev libffi-dev curl libressl-dev bash

WORKDIR /home/worker/app
COPY . /home/worker/app

RUN pip install -r requirements.txt
RUN pip install -e .

RUN adduser -D worker
RUN chown worker:worker -R /home/worker
USER worker
