# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain
# docker build -t eicdev/tdis-pre:latest .
# docker build -t eicdev/tdis-pre:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/tdis-pre:latest
#
# docker run --rm -it --init eicdev/tdis-pre:latest
# docker run --rm -it --init -p8888:8888 eicdev/tdis-pre:latest

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

# Create a user 'tdisuser' with sudo privileges
RUN useradd -m -G sudo tdisuser
RUN echo "tdisuser ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

# Create directories for container paths
RUN install -d -o tdisuser -g tdisuser ${CONTAINER_ROOT} && \
    install -d -o tdisuser -g tdisuser ${APP_ROOT} && \
    install -d -o tdisuser -g tdisuser /eic

USER tdisuser
WORKDIR /home/tdisuser
ENV PATH="$PATH:/home/tdisuser/.local/bin"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR ${APP_ROOT}

## For CI or final build steps (optional)
RUN apt-get update && \
    apt-get install -y clang-tools-18 clang-tidy dos2unix nlohmann-json3-dev&& \
    ln -s /usr/lib/llvm-18/bin/clang-scan-deps /usr/local/bin/clang-scan-deps && \
    rm -rf /var/lib/apt/lists/* \

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

#
# 2) ACTS
#
RUN edpm add acts && \
    edpm config acts branch=${VERSION_ACTS} && \
    edpm config acts cmake_flags="-DACTS_BUILD_EXAMPLES_PYTHON_BINDINGS=ON -DACTS_BUILD_PLUGIN_TGEO=ON -DACTS_BUILD_PLUGIN_DD4HEP=OFF -DACTS_BUILD_PLUGIN_JSON=ON -DACTS_BUILD_PLUGIN_ACTSVG=OFF" && \
    edpm install acts

#
# 3) PODIO
#
RUN edpm add podio && \
    edpm config podio branch=${VERSION_PODIO} && \
    edpm config podio cmake_flags="-DBUILD_TESTING=OFF" && \
    edpm install podio
#
#
# 4) JANA2
#
RUN edpm add jana2 && \
    edpm config jana2 branch=${VERSION_JANA2} && \
    edpm config jana2 cmake_flags="-DUSE_PODIO=On -DUSE_ROOT=On -DCMAKE_BUILD_TYPE=Debug" && \
    edpm install jana2
#
## Print a bit of info
#RUN ls && pwd
#
## (Optional) jupyterlab or other python packages
## RUN python3 -m pip install --user jupyterlab
#
#USER root
#
SHELL ["/bin/bash", "-c"]

# Create an entrypoint script that sources environment
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Source the EDPM environment script (env.sh)' >> /entrypoint.sh && \
    echo 'source /home/tdisuser/env.sh || true' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh
RUN chmod +x /entrypoint.sh



RUN dos2unix /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

#RUN echo "done"
