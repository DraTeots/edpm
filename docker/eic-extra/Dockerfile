# EIC extra tools layer (adds rucio client on top of eic-full)
#
# Replicates the rucio setup from the official EIC containers repo:
#   https://github.com/eic/containers/tree/master
#
# Build:
#   docker build -t eicdev/eic-extra:latest .
#   docker buildx build --tag eicdev/eic-extra:latest --push .
#
# Run:
#   docker run --rm -it --init eicdev/eic-extra:latest

#syntax=docker/dockerfile:1.10

FROM eicdev/eic-full:latest

WORKDIR ${APP_ROOT}

# ---------------------------------------------------------------------------#
#  Rucio client and EIC policy package                                       #
#                                                                            #
#  The official EIC containers (eic/containers) install these via Spack:    #
#    - py-rucio-clients @37.3.0: +argcomplete                               #
#    - py-eic-rucio-policy-package                                           #
#    - py-snakemake-storage-plugin-rucio @0.4.1:  (xl env only)             #
#                                                                            #
#  Here we replicate the same set via pip.                                   #
# ---------------------------------------------------------------------------#
RUN apt-get update && \
    apt-get install -y \
        libkrb5-dev \
    && apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    "rucio-clients>=37.3.0" \
    "argcomplete" \
    "eic-rucio-policy-package" \
    "snakemake-storage-plugin-rucio>=0.4.1"

# ---------------------------------------------------------------------------#
#  Rucio configuration                                                       #
#                                                                            #
#  Mirrors the config baked into the official EIC containers image at       #
#  /opt/rucio/etc/rucio.cfg — unprivileged read-only account.               #
# ---------------------------------------------------------------------------#
RUN mkdir -p /opt/rucio/etc

COPY rucio.cfg /opt/rucio/etc/rucio.cfg

ENV RUCIO_HOME=/opt/rucio

SHELL ["/bin/bash", "-c"]
