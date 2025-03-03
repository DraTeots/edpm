#
# docker build -t eicdev/tdis-pre:latest .
# docker build -t eicdev/tdis-pre:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/tdis-pre:latest
#
# docker run --rm -it --init eicdev/tdis-pre:latest
# docker run --rm -it --init -p8888:8888 eicdev/tdis-pre:latest

FROM ubuntu:noble

# Number of build threads
ARG BUILD_THREADS=8

# Software versions
ARG VERSION_CERN_ROOT=v6-32-06
ARG VERSION_ACTS=v37.4.0
ARG VERSION_PODIO=v01-01
ARG VERSION_JANA2=v2.4.0

ENV EIC_ROOT=/eic
ENV CONTAINER_ROOT=/container
ENV APP_ROOT=/container/app

SHELL ["/bin/bash", "-c"]

ARG DEBIAN_FRONTEND=noninteractive

# Install OS dependencies
RUN apt-get update &&\
    apt-get install -y python3-dev python3-pip python3-jinja2 python3-yaml python3-numpy   \
                       sudo git cmake gdb ninja-build apt-utils bash ccache clang valgrind  gfortran g++ gcc curl \
                       dialog apt-utils dpkg-dev tzdata binutils \
                       libvtk9-dev libmsgsl-dev libftgl-dev libxml2-dev libldap2-dev  \
                       libgsl0-dev libfftw3-dev libmysqlclient-dev libavahi-compat-libdnssd-dev libssl-dev  \
                       libcfitsio-dev xlibmesa-glu-dev libkrb5-dev graphviz-dev libpcre3-dev libglew-dev  \
                       libxmu-dev libexpat-dev libtbb-dev libboost-filesystem-dev libboost-all-dev \
                       libspdlog-dev libxext-dev qtbase5-dev libqt5opengl5-dev libx11-dev libboost-test-dev  \
                       libocct-draw-dev libeigen3-dev libocct-data-exchange-dev libocct-foundation-dev  \
                       libfmt-dev libxft-dev libboost-program-options-dev libboost-dev libxpm-dev   \
                       libxerces-c3-dev occt-misc libvdt-dev libglu1-mesa-dev libgraphviz-dev \
                       libgsl-dev qtwebengine5-dev nlohmann-json3-dev &&\
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# EnvSet clang as default
RUN update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-18 60

# Create a user 'tdisuser' with sudo privileges
RUN useradd -m -G sudo tdisuser
RUN echo "tdisuser ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

# Create directories for container paths
RUN install -d -o tdisuser -g tdisuser ${CONTAINER_ROOT} && \
    install -d -o tdisuser -g tdisuser ${APP_ROOT} && \
    install -d -o tdisuser -g tdisuser /eic

USER tdisuser
WORKDIR /home/tdisuser
ENV PATH "$PATH:/home/tdisuser/.local/bin"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages ruamel.yaml click appdirs edpm &&\
    edpm --top-dir=/container/app &&\
    edpm

# Initialize a brand-new EDPM plan (plan.edpm.yaml) if none exists
RUN edpm init --force

# Configure global settings
RUN edpm config global cxx_standard=20 &&\
    echo "*** EDPM CONFIGURED ***"

#
# 1) ROOT
#
RUN edpm add root && \
    edpm config root branch=${VERSION_CERN_ROOT} && \
    edpm config root cmake_custom_flags="-Dcuda=OFF -Dcudnn=OFF -Dtmva-gpu=OFF" && \
    edpm install -j${BUILD_THREADS} root && \
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
# 4) JANA2
#
RUN edpm add jana2 && \
    edpm config jana2 branch=${VERSION_JANA2} && \
    edpm config jana2 cmake_flags="-DUSE_PODIO=On -DUSE_ROOT=On -DCMAKE_BUILD_TYPE=Debug" && \
    edpm install jana2

# Print a bit of info
RUN ls && pwd

# (Optional) jupyterlab or other python packages
# RUN python3 -m pip install --user jupyterlab

USER root

# Create an entrypoint script that sources environment
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Source the EDPM environment script (env.sh)' >> /entrypoint.sh && \
    echo 'source /home/tdisuser/env.sh || true' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# For CI or final build steps (optional)
RUN apt-get update && \
    apt-get install -y clang-tools-18 clang-tidy && \
    ln -s /usr/lib/llvm-18/bin/clang-scan-deps /usr/local/bin/clang-scan-deps && \
    rm -rf /var/lib/apt/lists/*

RUN echo "done"
