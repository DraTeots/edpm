# Full EIC software stack (adds EPIC geometry and EICrecon on top of eic-base)
#
# Build:
#   docker build -t eicdev/eic-full:latest .
#   docker build -t eicdev/eic-full:latest --build-arg BUILD_THREADS=24 .
#   docker buildx build --tag eicdev/eic-full:latest --push .
#
# Run:
#   docker run --rm -it --init eicdev/eic-full:latest
#
# Build with buildx debug:
#   BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain
#   In PowerShell:  $env:BUILDX_EXPERIMENTAL="1"

FROM eicdev/eic-base:latest

WORKDIR ${APP_ROOT}

# ---------------------------------------------------------------------------#
#  Build-time arguments & environment                                        #
# ---------------------------------------------------------------------------#
ARG BUILD_THREADS=8
ARG CXX_STANDARD=20


### ---------------------------------------------------------------------- ###
###          EPIC build (ePIC detector geometry)                            ###
### ---------------------------------------------------------------------- ###
ARG VERSION_EPIC=25.02.0
ENV EPIC_SRC_PATH=${APP_ROOT}/epic-src \
    EPIC_BLD_PATH=${APP_ROOT}/epic-build \
    EPIC_INS_PATH=${APP_ROOT}/epic

RUN set -ex && \
    git clone --branch ${VERSION_EPIC} --depth 1 https://github.com/eic/epic.git "${EPIC_SRC_PATH}" && \
    mkdir -p "${EPIC_BLD_PATH}" && cd "${EPIC_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${EPIC_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${EPIC_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${EPIC_BLD_PATH}" "${EPIC_SRC_PATH}"

ENV DETECTOR_PATH="${EPIC_INS_PATH}/share/epic" \
    BEAMLINE=epic \
    BEAMLINE_PATH="${EPIC_INS_PATH}/share/epic" \
    BEAMLINE_CONFIG=epic \
    PATH="${EPIC_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${EPIC_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${EPIC_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          EICrecon build (EIC Reconstruction Framework)                  ###
### ---------------------------------------------------------------------- ###
ARG VERSION_EICRECON=main
ENV EICRECON_SRC_PATH=${APP_ROOT}/eicrecon-src \
    EICRECON_BLD_PATH=${APP_ROOT}/eicrecon-build \
    EICRECON_INS_PATH=${APP_ROOT}/eicrecon

RUN set -ex && \
    git clone --branch ${VERSION_EICRECON} --depth 1 https://github.com/eic/eicrecon.git "${EICRECON_SRC_PATH}" && \
    mkdir -p "${EICRECON_BLD_PATH}" && cd "${EICRECON_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${EICRECON_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${EICRECON_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${EICRECON_BLD_PATH}" "${EICRECON_SRC_PATH}"

ENV eicrecon_HOME=${EICRECON_INS_PATH} \
    JANA_PLUGIN_PATH="${EICRECON_INS_PATH}/lib/EICrecon/plugins:${JANA_PLUGIN_PATH}" \
    PATH="${EICRECON_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${EICRECON_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${EICRECON_INS_PATH}:${CMAKE_PREFIX_PATH}"


SHELL ["/bin/bash", "-c"]
