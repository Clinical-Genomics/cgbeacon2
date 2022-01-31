###########
# BUILDER #
###########
FROM frolvlad/alpine-miniconda3 AS python-builder

# Install required libs
RUN apk update && \
    apk --no-cache add gcc g++ curl libcurl curl-dev zlib-dev bzip2-dev xz-dev

# Install bedtools using conda
RUN conda update -n base -c defaults conda && conda install -c bioconda bedtools

# Install app dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


#########
# FINAL #
#########
FROM frolvlad/alpine-miniconda3

LABEL about.license="MIT License (MIT)"
LABEL about.home="https://github.com/Clinical-Genomics/cgbeacon2"
LABEL about.documentation="https://clinical-genomics.github.io/cgbeacon2"
LABEL about.tags="beacon,Rare diseases,VCF,variants,SNP,NGS"

# Copy conda environment from builder
COPY --from=python-builder /opt/conda/. /opt/conda/

WORKDIR /home/worker/app
COPY . /home/worker/app

# Install the app
RUN pip install --no-cache-dir -e .

# Run commands as non-root user
RUN adduser -D worker

# Grant non-root user permissions over the working directory
RUN chown worker:worker -R /home/worker

USER worker

ENTRYPOINT ["beacon"]
