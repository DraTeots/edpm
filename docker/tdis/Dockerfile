# BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain .
# in PShell instead of  BUILDX_EXPERIMENTAL=1 use:
#   $env:BUILDX_EXPERIMENTAL="1"
# docker buildx build --tag eicdev/tdis:latest --push .
# docker build -t eicdev/tdis:latest .
# docker build -t eicdev/tdis:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/tdis:latest
#
# docker run --rm -it --init eicdev/tdis:latest
# docker run --rm -it --init -p8888:8888 eicdev/tdis:latest

FROM eicdev/tdis-pre:latest


# Install EDPM v3 and set the top_dir
RUN python3 -m pip install --user --upgrade --force-reinstall --break-system-packages edpm

WORKDIR ${APP_ROOT}

RUN git clone https://github.com/JeffersonLab/tdis.git tdis-src


WORKDIR ${APP_ROOT}/tdis-src
# -DCMAKE_INSTALL_PREFIX is the key directive to control the install location.
RUN source /app/env.sh && cmake -B build -S . -DCMAKE_INSTALL_PREFIX=${APP_ROOT}/tdis-install -Dpodio_DIR="/app/podio/podio-install/lib/cmake/podio" -DJANA_DIR="/app/jana2/jana2-install/lib/JANA/cmake"
# Build the application using all available processor cores for speed.
RUN cmake --build build -- -j1
# Install the compiled application to the specified prefix.
RUN cmake --install build

# Step 6: Add the 'bin' directory of our new installation to the system's PATH.
# This makes the executables available directly from the command line.
ENV PATH=${APP_ROOT}/tdis-install/bin:${PATH}

WORKDIR /root
