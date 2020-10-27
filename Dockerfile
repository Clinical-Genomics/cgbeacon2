FROM python:3.8-alpine3.12

LABEL version="1"
LABEL about.license="MIT License (MIT)"
LABEL software.version="1.3"
LABEL about.home="https://github.com/Clinical-Genomics/cgbeacon2"
LABEL maintainer="Chiara Rasi <chiara.rasi@scilifelab.se>"

RUN apk update
# Install required libs
RUN apk --no-cache add make automake gcc g++ linux-headers curl libcurl curl-dev \
  zlib-dev bzip2-dev xz-dev libffi-dev curl libressl-dev bash git

# Install bedtools
RUN git clone https://github.com/arq5x/bedtools2.git && \
	cd bedtools2 &&  \
	make && \
	make install && \
	cd .. && \
	rm -rf bedtools2

WORKDIR /home/worker/app
COPY . /home/worker/app

# Install requirements
RUN pip install -r requirements.txt

# Install the app
RUN pip install -e .

# Run commands as non-root user
RUN adduser -D worker
RUN chown worker:worker -R /home/worker
USER worker
