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

# ----- ENV for acts -----
ENV ACTS_DIR=/app/acts/acts-install \
    LD_LIBRARY_PATH=/app/acts/acts-install/lib:${LD_LIBRARY_PATH} \
    CMAKE_PREFIX_PATH=/app/acts/acts-install/lib/cmake/Acts:/app/acts/acts-install/lib/cmake/nlohmann_json:/app/acts/acts-install/lib/cmake/ActsDD4hep:${CMAKE_PREFIX_PATH}


# -------------------
# JANA2
# -------------------
ARG VERSION_JANA2=v2.4.1
RUN edpm add jana2 && \
   edpm config jana2 branch=${VERSION_JANA2} && \
   edpm config jana2 cmake_flags="-DUSE_PODIO=On -DUSE_ROOT=On -DCMAKE_BUILD_TYPE=Debug" && \
   edpm install jana2

###############################################################################
# ----- ENV for acts -----
ENV ACTS_DIR=/app/acts/acts-install \
    LD_LIBRARY_PATH=/app/acts/acts-install/lib:${LD_LIBRARY_PATH} \
    CMAKE_PREFIX_PATH=/app/acts/acts-install/lib/cmake/Acts:/app/acts/acts-install/lib/cmake/nlohmann_json:/app/acts/acts-install/lib/cmake/ActsDD4hep:${CMAKE_PREFIX_PATH}

###############################################################################
# ----- ENV for catch2 -----
ENV LD_LIBRARY_PATH=/app/catch2/catch2-install/lib:${LD_LIBRARY_PATH} \
    CMAKE_PREFIX_PATH=/app/catch2/catch2-install/lib/cmake/Catch2:${CMAKE_PREFIX_PATH}

###############################################################################
# ----- ENV for eigen3 -----
ENV CMAKE_PREFIX_PATH=/app/eigen3/eigen3-install/share/eigen3/cmake:${CMAKE_PREFIX_PATH}

###############################################################################
# ----- ENV for fmt -----
ENV LD_LIBRARY_PATH=/app/fmt/fmt-install/lib:${LD_LIBRARY_PATH} \
    CMAKE_PREFIX_PATH=/app/fmt/fmt-install/lib/cmake/fmt:${CMAKE_PREFIX_PATH}

###############################################################################
# ----- ENV for hepmc3 -----
ENV PATH=/app/hepmc3/hepmc3-install/bin:${PATH} \
    HEPMC3_DIR=/app/hepmc3/hepmc3-install \
    CMAKE_PREFIX_PATH=/app/hepmc3/hepmc3-install/share/HepMC3/cmake:${CMAKE_PREFIX_PATH} \
    LD_LIBRARY_PATH=/app/hepmc3/hepmc3-install/lib:${LD_LIBRARY_PATH}

###############################################################################
# ----- ENV for jana2 -----
ENV JANA_HOME=/app/jana2/jana2-install \
    JANA_PLUGIN_PATH=/app/jana2/jana2-install/plugins \
    PATH=/app/jana2/jana2-install/bin:${PATH} \
    LD_LIBRARY_PATH=/app/jana2/jana2-install/lib:${LD_LIBRARY_PATH} \
    CMAKE_PREFIX_PATH=/app/jana2/jana2-install/lib/cmake/JANA:${CMAKE_PREFIX_PATH}

###############################################################################
# ----- ENV for podio -----
ENV PODIO_ROOT=/app/podio/podio-install \
    LD_LIBRARY_PATH=/app/podio/podio-install/lib:${LD_LIBRARY_PATH} \
    CMAKE_PREFIX_PATH=/app/podio/podio-install/lib/cmake/podio:${CMAKE_PREFIX_PATH}

###############################################################################
# ----- ENV for root -----
ENV CMAKE_PREFIX_PATH=/app/root/root-install/cmake:${CMAKE_PREFIX_PATH}

#
SHELL ["/bin/bash", "-c"]

# Create an entrypoint script that sources environment
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Source the EDPM environment script (env.sh)' >> /entrypoint.sh && \
    echo 'source /app/env.sh || true' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh
RUN chmod +x /entrypoint.sh



RUN dos2unix /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

#RUN echo "done"
