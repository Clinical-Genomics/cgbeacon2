###########
# BUILDER #
###########
FROM clinicalgenomics/python3.8-slim-bullseye-bedtools-venv:1.0 AS python-builder

ENV PATH="/venv/bin:$PATH"

# Install dependencies
COPY . /temp

WORKDIR /temp
RUN pip install --no-cache-dir -r requirements.txt


#########
# FINAL #
#########
FROM clinicalgenomics/python3.8-slim-bullseye-venv:1.0 

LABEL about.license="MIT License (MIT)"
LABEL about.home="https://github.com/Clinical-Genomics/cgbeacon2"
LABEL about.documentation="https://clinical-genomics.github.io/cgbeacon2"
LABEL about.tags="beacon,Rare diseases,VCF,variants,SNP,NGS"

# Do not upgrade to the latest pip version to ensure more reproducible builds
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PATH="/venv/bin:$PATH"
RUN echo export PATH="/venv/bin:\$PATH" > /etc/profile.d/venv.sh

# Copy the folder where bedtools was installed from builder image
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Create a non-root user to run commands
RUN groupadd --gid 1000 worker && useradd -g worker --uid 1000 --shell /usr/sbin/nologin --create-home worker

# Copy virtual environment from builder
COPY --chown=worker:worker --from=python-builder /venv /venv

# Copy app dir to image
COPY --chown=worker:worker . /home/worker/app

WORKDIR /home/worker/app

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# Install the app
RUN pip install --no-cache-dir -e .

# Run the app as non-root user
USER worker

ENTRYPOINT ["beacon"]
