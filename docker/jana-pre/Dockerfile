# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain .
# docker build -t eicdev/jana-pre:latest .
# docker build -t eicdev/jana-pre:latest --progress=plain --build-arg BUILD_THREADS=24 .
# docker build -t codecr.jlab.org/epsci/jsro_toolkit/jana-pre:latest


# docker push eicdev/jana-pre:latest
# docker tag eicdev/jana-pre:latest codecr.jlab.org/epsci/jsro_toolkit/jana-pre:latest
# docker push codecr.jlab.org/epsci/jsro_toolkit/jana-pre:latest
#
# docker run --rm -it --init eicdev/jana-pre:latest
# docker run --rm -it --init -p8888:8888 eicdev/jana-pre:latest

FROM eicdev/ubuntu-dev:latest

# Number of build threads
ARG BUILD_THREADS=8

# Software versions
ARG VERSION_CERN_ROOT=v6-34-04
ARG VERSION_ACTS=v37.4.0
ARG VERSION_PODIO=v01-01
ARG VERSION_JANA2=v2.4.0

ENV CONTAINER_ROOT=/opt
ENV APP_ROOT=/opt


WORKDIR ${APP_ROOT}
ENV PATH="$PATH:/root/.local/bin"


# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages ruamel.yaml click appdirs edpm

# this is where our edpm plan will be
ENV EDPM_PLAN_FILE=${APP_ROOT}/plan.edpm.yaml
ENV EDPM_LOCK_FILE=${APP_ROOT}/plan-lock.edpm.yaml


RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages ruamel.yaml click appdirs edpm

#RUN apt-get update &&\
#    apt-get install -y nlohmann-json3-dev liblz4-dev &&\
#    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \

#
# PODIO and event data models
#
RUN edpm add podio@${VERSION_PODIO} &&\
    edpm config podio cmake_flags="-DBUILD_TESTING=OFF" &&\
    edpm install podio

RUN edpm add edm4hep &&\
    edpm config edm4hep cmake_user_flags="-DEDM4HEP_WITH_JSON=OFF -Dnlohmann_json_DIR=/usr" \

RUN edpm add edm4eic &&\
    edpm config edm4eic cmake_user_flags="-Dnlohmann_json_DIR=/usr"&&\
    edpm install

#
# EVIO
#
RUN edpm add disruptor-cpp  &&\
    edpm install disruptor-cpp  &&\
    edpm add evio &&\
    edpm config evio url="https://github.com/DraTeots/evio.git"&&\
    edpm config evio branch="cmake-updates"&&\
    edpm config evio cmake_user_flags="-DDISRUPTOR_CPP_DIR=/opt/disruptor-cpp/disruptor-cpp-install"&&\
    edpm install

#
# JANA2
#
RUN edpm add jana2 && \
    edpm config jana2 branch=${VERSION_JANA2} && \
    edpm config jana2 cmake_flags="-DUSE_PODIO=On -DUSE_ROOT=On -DCMAKE_BUILD_TYPE=Debug" && \
    edpm install

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

RUN edpm env save

## Create an entrypoint script that sources environment
#RUN cat <<'EOF' > /entrypoint.sh
##!/bin/sh
#set -e
#
## Source the EDPM environment script (env.sh)!
#source ${APP_ROOT}/env.sh || true
#
#exec "$@"
#EOF

# For use of ${APP_ROOT} and possibly other variables we are not using cat <<'EOF' approach
RUN echo '#!/bin/bash'                                    > /entrypoint.sh &&\
    echo 'set -e'                                        >> /entrypoint.sh &&\
    echo ''                                              >> /entrypoint.sh &&\
    echo '# Source the EDPM environment script (env.sh)' >> /entrypoint.sh &&\
    echo 'source ${APP_ROOT}/env.sh || true'             >> /entrypoint.sh &&\
    echo ''                                              >> /entrypoint.sh &&\
    echo 'exec "$@"'                                     >> /entrypoint.sh
#
RUN chmod +x /entrypoint.sh
RUN ls -l /entrypoint.sh  # Verify file exists
RUN cat /entrypoint.sh    # Verify content
RUN dos2unix /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
#
## For CI or final build steps (optional)
#RUN apt-get update && \
#    apt-get install -y clang-tools-18 clang-tidy && \
#    ln -s /usr/lib/llvm-18/bin/clang-scan-deps /usr/local/bin/clang-scan-deps && \
#    rm -rf /var/lib/apt/lists/*
#
#RUN echo "done"
