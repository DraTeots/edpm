# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain .
# docker build -t eicdev/jsro-pre:latest .
# docker build -t eicdev/jsro-pre:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/jsro-pre:latest
#
# docker run --rm -it --init eicdev/jsro-pre:latest
# docker run --rm -it --init -p8888:8888 eicdev/jsro-pre:latest

FROM eicdev/ubuntu-dev:latest

# Number of build threads
ARG BUILD_THREADS=8

# Software versions
ARG VERSION_CERN_ROOT=v6-34-04
ARG VERSION_ACTS=v37.4.0
ARG VERSION_PODIO=v01-01
ARG VERSION_JANA2=v2.4.0

ENV EIC_ROOT=/eic
ENV CONTAINER_ROOT=/container
ENV APP_ROOT=/container/app

ARG DEBIAN_FRONTEND=noninteractive

ENV EDPM_PLAN_FILE=${APP_ROOT}/edpm-plan.yaml
ENV EDPM_PLAN_FILE=${APP_ROOT}/edpm-plan.yaml

# Create a user 'jsrouser' with sudo privileges
RUN useradd -m -G sudo jsrouser
RUN echo "jsrouser ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

# Create directories for container paths
RUN install -d -o jsrouser -g jsrouser ${CONTAINER_ROOT} && \
    install -d -o jsrouser -g jsrouser ${APP_ROOT} && \
    install -d -o jsrouser -g jsrouser /eic

USER jsrouser
WORKDIR /home/jsrouser
ENV PATH="$PATH:/home/jsrouser/.local/bin"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR ${APP_ROOT}

# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages ruamel.yaml click appdirs edpm

# Initialize a brand-new EDPM plan (plan.edpm.yaml) if none exists
RUN edpm init --force && edpm --top-dir=${APP_ROOT}

# Configure global settings
RUN edpm config global cxx_standard=20 &&\
    edpm config global build_threads=${BUILD_THREADS} &&\
    echo "*** EDPM CONFIGURED ***"

RUN edpm add catch2 && \
    edpm install catch2 && \
    edpm clean catch2

#
# 1) ROOT
#
RUN edpm add root@${VERSION_CERN_ROOT} && \
    edpm config root cmake_custom_flags="-Dcuda=OFF -Dcudnn=OFF -Dtmva-gpu=OFF" && \
    edpm install root && \
    edpm clean root

RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages ruamel.yaml click appdirs edpm
#
# 3) PODIO
#
RUN edpm add podio@${VERSION_PODIO} &&\
    edpm config podio cmake_flags="-DBUILD_TESTING=OFF" &&\
    edpm add edm4hep &&\
    edpm add edm4eic &&\
    edpm install

#
# EVIO
#
RUN edpm add disruptor-cpp  &&\
    edpm add evio &&\
    edpm install

#
# 4) JANA2
#
RUN edpm add jana2 && \
    edpm config jana2 branch=${VERSION_JANA2} && \
    edpm config jana2 cmake_flags="-DUSE_PODIO=On -DUSE_ROOT=On -DCMAKE_BUILD_TYPE=Debug" && \
    edpm install jana2

# Print a bit of info
RUN ls && pwd
#
## (Optional) jupyterlab or other python packages
## RUN python3 -m pip install --user jupyterlab
#
#USER root
#
#SHELL ["/bin/bash", "-c"]
#
## Create an entrypoint script that sources environment
#RUN echo '#!/bin/bash' > /entrypoint.sh && \
#    echo 'set -e' >> /entrypoint.sh && \
#    echo '' >> /entrypoint.sh && \
#    echo '# Source the EDPM environment script (env.sh)' >> /entrypoint.sh && \
#    echo 'source /home/jsrouser/env.sh || true' >> /entrypoint.sh && \
#    echo '' >> /entrypoint.sh && \
#    echo 'exec "$@"' >> /entrypoint.sh
#
#RUN chmod +x /entrypoint.sh
#ENTRYPOINT ["/entrypoint.sh"]
#
## For CI or final build steps (optional)
#RUN apt-get update && \
#    apt-get install -y clang-tools-18 clang-tidy && \
#    ln -s /usr/lib/llvm-18/bin/clang-scan-deps /usr/local/bin/clang-scan-deps && \
#    rm -rf /var/lib/apt/lists/*
#
#RUN echo "done"
