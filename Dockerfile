FROM frolvlad/alpine-miniconda3

LABEL base_image="frolvlad/alpine-miniconda3"
LABEL about.license="MIT License (MIT)"
LABEL about.home="https://github.com/Clinical-Genomics/cgbeacon2"
LABEL about.documentation="http://www.clinicalgenomics.se/cgbeacon2"
LABEL about.tags="beacon,Rare diseases,VCF,variants,SNP,NGS"

# Install bedtools using conda
RUN conda update -n base -c defaults conda && conda install -c bioconda bedtools

# Install required libs
RUN apk update \
	&& apk --no-cache add gcc g++ curl libcurl curl-dev zlib-dev bzip2-dev xz-dev \
    bash python3

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

ENTRYPOINT ["cgbeacon2"]
