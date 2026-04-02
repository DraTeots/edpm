# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain .
# in PShell instead of  BUILDX_EXPERIMENTAL=1 use:
#   $env:BUILDX_EXPERIMENTAL="1"
# docker buildx build --tag eicdev/meson-structure:latest --push .
# docker build -t eicdev/meson-structure:latest .
# docker build -t eicdev/meson-structure:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/meson-structure:latest
#
# docker run --rm -it --init eicdev/meson-structure:latest
# docker run --rm -it --init -p8888:8888 eicdev/meson-structure:latest

FROM eicdev/ubuntu-root:latest


WORKDIR ${APP_ROOT}

# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages edpm


# Add and instantly install
RUN edpm install -a fmt@11.2.0


RUN edpm install -a catch2 && \
    edpm clean catch2


# -------------------
#   P O D I O
# -------------------
ARG VERSION_PODIO=v01-02
RUN edpm add podio && \
    edpm config podio branch=${VERSION_PODIO} && \
    edpm config podio cmake_flags="-DBUILD_TESTING=OFF -DENABLE_RNTUPLE=ON" && \
    edpm install podio && \
    edpm clean podio


# Install OS dependencies
RUN apt-get update &&\
    apt-get install -y libfmt-dev libboost-filesystem-dev libboost-all-dev libspdlog-dev libboost-test-dev libxmu-dev libexpat-dev libtbb-dev nlohmann-json3-dev pybind11-json-dev &&\
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*


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

RUN apt-get update &&\
    sudo apt install -y nlohmann-json3-dev pybind11-json-dev &&\
    apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

RUN edpm add edm4hep &&\
    edpm config edm4hep cmake_user_flags="-DEDM4HEP_WITH_JSON=OFF" &&\
    edpm config edm4hep branch=v00-99-01 &&\
    edpm install edm4hep &&\
    edpm clean edm4hep

RUN edpm install -a edm4eic@v8.2.0 && edpm clean edm4eic


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
