# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain .
# in PShell instead of  BUILDX_EXPERIMENTAL=1 use:
#   $env:BUILDX_EXPERIMENTAL="1"
# docker buildx build --tag eicdev/tdis-pre:latest --push .
# docker build -t eicdev/tdis-pre:latest .
# docker build -t eicdev/tdis-pre:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/tdis-pre:latest
#
# docker run --rm -it --init eicdev/tdis-pre:latest
# docker run --rm -it --init -p8888:8888 eicdev/tdis-pre:latest

FROM eicdev/ubuntu-root:latest


WORKDIR ${APP_ROOT}

# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages edpm


# Add and instantly install
RUN edpm install -a fmt@11.2.0


RUN edpm add catch2 && \
    edpm install catch2 && \
    edpm clean catch2


# -------------------
#   P O D I O
# -------------------
ARG VERSION_PODIO=v01-03
RUN edpm add podio && \
    edpm config podio branch=${VERSION_PODIO} && \
    edpm config podio cmake_flags="-DBUILD_TESTING=OFF" && \
    edpm install podio && \
    edpm clean podio


# Install OS dependencies
RUN apt-get update &&\
    apt-get install -y libfmt-dev libboost-filesystem-dev libboost-all-dev libspdlog-dev libboost-test-dev libxmu-dev libexpat-dev libtbb-dev &&\
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# -------------------
# ACTS
# -------------------
ARG VERSION_ACTS=v41.0.0
RUN edpm install -a eigen3@3.4.0 && edpm clean eigen3
RUN edpm add hepmc3 && \
    edpm config hepmc3 version=3.3.1 \
    edpm config hepmc3 cmake_user_flags="\
    -DHEPMC3_ENABLE_PYTHON:BOOL=OFF \
    -DPython_LIBRARIES=/usr/lib/python3.12/config-3.12-x86_64-linux-gnu \
    -DPython_EXECUTABLE=/usr/bin/python3 \
    -DPython_INCLUDE_DIRS=/usr/include/python3.12 \
    " && \
    edpm install hepmc3 && \
    edpm clean hepmc3

RUN edpm add acts && \
    edpm config acts branch=${VERSION_ACTS} && \
    edpm config acts cmake_flags=" \
    -DACTS_BUILD_PLUGIN_TGEO=ON \
    -DACTS_BUILD_PLUGIN_JSON=ON  \
    -DACTS_BUILD_EXAMPLES_PYTHON_BINDINGS=ON \
    -DACTS_BUILD_PLUGIN_TGEO=ON  \
    -DACTS_BUILD_PLUGIN_ACTSVG=OFF \
    -DACTS_BUILD_PLUGIN_DD4HEP=OFF \
    " && \
    edpm install acts &&\
    edpm clean acts


# -------------------
# JANA2
# -------------------
ARG VERSION_JANA2=v2.4.1
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
