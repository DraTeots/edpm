# Main build command - minimal and self-contained
  #BUILDX_GIT_LABELS=full docker buildx build \
  #    --platform linux/amd64,linux/arm64 \
  #    --tag eicdev/ubuntu-root:latest \
  #    --push \
  #    .
# One line:
# BUILDX_GIT_LABELS=full docker buildx build --tag eicdev/ubuntu-root:latest --push .

FROM ubuntu:latest

# OCI Image Labels - most automatically populated by buildx via BUILDX_GIT_LABELS
LABEL org.opencontainers.image.authors="Dmitry Romanov <romanov@jlab.org>" \
      org.opencontainers.image.url="https://github.com/eic/ubuntu-root" \
      org.opencontainers.image.documentation="https://github.com/eic/ubuntu-root/blob/main/README.md" \
      org.opencontainers.image.vendor="EIC Software" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.title="EIC Ubuntu Development Environment with ROOT" \
      org.opencontainers.image.description="Ubuntu-based development container with CERN ROOT, scientific computing libraries, and development tools for EIC software development"

# Note: The following labels are automatically added by buildx when BUILDX_GIT_LABELS=full:
# - org.opencontainers.image.source (git repository URL)
# - org.opencontainers.image.revision (git commit hash)
# - com.docker.image.source.entrypoint (Dockerfile location)

# Legacy labels for compatibility
LABEL maintainer.name="Dmitry Romanov" \
      maintainer.email="romanov@jlab.org"

ARG DEBIAN_FRONTEND=noninteractive

## With heredocs for multi-line scripts, we want to fail on error and the print failing line.
## Ref: https://docs.docker.com/engine/reference/builder/#example-running-a-multi-line-script
SHELL ["bash", "-ex", "-c"]

ENV CLICOLOR_FORCE=1      \
    LANGUAGE=en_US.UTF-8  \
    LANG=en_US.UTF-8      \
    LC_ALL=en_US.UTF-8

# Install OS dependencies
RUN apt-get update &&\
    apt-get install -y python3-dev python3-pip python3-jinja2 python3-yaml python3-numpy  dos2unix \
                       sudo git cmake gdb ninja-build apt-utils bash ccache clang valgrind gfortran g++ gcc curl clang-tools-18 clang-tidy-18 \
                       dialog apt-utils dpkg-dev tzdata binutils unminimize\
                       libftgl-dev libxml2-dev libldap2-dev  \
                       libfftw3-dev libmysqlclient-dev libavahi-compat-libdnssd-dev  \
                       libcfitsio-dev libglu1-mesa-dev libkrb5-dev libpcre3-dev libglew-dev  \
                       libgraphviz-dev \
                       libgsl-dev qtwebengine5-dev nlohmann-json3-dev liblz4-dev \
                       libgl2ps-dev liblzma-dev libxxhash-dev libzstd-dev &&\
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY bashrc /root/.bashrc
RUN dos2unix /root/.bashrc

# Set clang as default
RUN update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-18 60

# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages ruamel.yaml click appdirs edpm

RUN yes | unminimize

ENV APP_ROOT=/app

WORKDIR ${APP_ROOT}
ENV PATH="$PATH:/root/.local/bin"

# Number of build threads
ARG BUILD_THREADS=8

# Software versions
ARG VERSION_CERN_ROOT=v6-34-04

# this is where our edpm plan will be
ENV EDPM_PLAN_FILE=${APP_ROOT}/plan.edpm.yaml
ENV EDPM_LOCK_FILE=${APP_ROOT}/plan-lock.edpm.yaml

# Initialize EDPM and configure global settings
RUN edpm init &&\
    edpm --top-dir=${APP_ROOT} &&\
    edpm config global cxx_standard=20 &&\
    edpm config global build_threads=${BUILD_THREADS} &&\
    edpm config global env_bash_out=${APP_ROOT}/env.sh &&\
    edpm config global env_csh_out="" &&\
    edpm config global cmake_toolchain_out=${APP_ROOT}/CMakeToolchain.cmake &&\
    edpm config global cmake_presets_out=${APP_ROOT}/CMakeUserPresets.json &&\
    edpm env save &&\
    echo "*** EDPM CONFIGURED ***"

RUN edpm add root@${VERSION_CERN_ROOT} && \
    edpm config root cmake_custom_flags="-Dcuda=OFF -Dcudnn=OFF -Dtmva-gpu=OFF" && \
    edpm install root && \
    edpm clean root

CMD ["bash", "-c"]

RUN echo '#!/bin/bash'                                    > /entrypoint.sh &&\
    echo 'set -e'                                        >> /entrypoint.sh &&\
    echo ''                                              >> /entrypoint.sh &&\
    echo '# Source the EDPM environment script (env.sh)' >> /entrypoint.sh &&\
    echo 'source ${APP_ROOT}/env.sh || true'             >> /entrypoint.sh &&\
    echo ''                                              >> /entrypoint.sh &&\
    echo 'exec "$@"'                                     >> /entrypoint.sh

RUN chmod +x /entrypoint.sh
RUN ls -l /entrypoint.sh  # Verify file exists
RUN cat /entrypoint.sh    # Verify content
RUN dos2unix /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]