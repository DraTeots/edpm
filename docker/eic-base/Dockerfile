# EIC base software stack (everything except EPIC geometry and EICrecon)
#
# Build:
#   docker build -t eicdev/eic-base:latest .
#   docker build -t eicdev/eic-base:latest --build-arg BUILD_THREADS=24 .
#   docker buildx build --tag eicdev/eic-base:latest --push .
#
# Run:
#   docker run --rm -it --init eicdev/eic-base:latest
#
# Build with buildx debug:
#   BUILDX_EXPERIMENTAL=1 docker buildx debug --invoke bash build --progress=plain
#   In PowerShell:  $env:BUILDX_EXPERIMENTAL="1"

FROM eicdev/ubuntu-root:latest

WORKDIR ${APP_ROOT}

# ---------------------------------------------------------------------------#
#  Build-time arguments & environment                                        #
# ---------------------------------------------------------------------------#
ARG BUILD_THREADS=8
ARG CXX_STANDARD=20

# ---------------------------------------------------------------------------#
#  OS dependencies (beyond what ubuntu-root provides)                        #
# ---------------------------------------------------------------------------#
RUN apt-get update && \
    apt-get install -y \
        libxerces-c3-dev libexpat-dev qtbase5-dev libqt5opengl5-dev libxmu-dev \
        libspdlog-dev libtbb-dev libboost-all-dev \
        libocct-foundation-dev occt-misc libocct-draw-dev libocct-data-exchange-dev \
    && apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*


### ---------------------------------------------------------------------- ###
###          CLHEP build                                                   ###
### ---------------------------------------------------------------------- ###
ARG VERSION_CLHEP=CLHEP_2_4_7_1
ENV CLHEP_SRC_PATH=${APP_ROOT}/clhep-src \
    CLHEP_BLD_PATH=${APP_ROOT}/clhep-build \
    CLHEP_INS_PATH=${APP_ROOT}/clhep

RUN set -ex && \
    git clone --branch ${VERSION_CLHEP} --depth 1 https://gitlab.cern.ch/CLHEP/CLHEP.git "${CLHEP_SRC_PATH}" && \
    mkdir -p "${CLHEP_BLD_PATH}" && cd "${CLHEP_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${CLHEP_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${CLHEP_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${CLHEP_BLD_PATH}" "${CLHEP_SRC_PATH}"

ENV CLHEP=${CLHEP_INS_PATH} \
    CLHEP_BASE_DIR=${CLHEP_INS_PATH} \
    CLHEP_INCLUDE_DIR="${CLHEP_INS_PATH}/include" \
    CLHEP_LIB_DIR="${CLHEP_INS_PATH}/lib" \
    PATH="${CLHEP_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${CLHEP_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${CLHEP_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          Eigen3 build                                                  ###
### ---------------------------------------------------------------------- ###
ARG VERSION_EIGEN3=3.4.0
ENV EIGEN3_SRC_PATH=${APP_ROOT}/eigen3-src \
    EIGEN3_BLD_PATH=${APP_ROOT}/eigen3-build \
    EIGEN3_INS_PATH=${APP_ROOT}/eigen3

RUN set -ex && \
    git clone --branch ${VERSION_EIGEN3} --depth 1 https://gitlab.com/libeigen/eigen.git "${EIGEN3_SRC_PATH}" && \
    mkdir -p "${EIGEN3_BLD_PATH}" && cd "${EIGEN3_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${EIGEN3_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      "${EIGEN3_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${EIGEN3_BLD_PATH}" "${EIGEN3_SRC_PATH}"

ENV CMAKE_PREFIX_PATH="${EIGEN3_INS_PATH}/share/eigen3/cmake:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          Catch2 build                                                  ###
### ---------------------------------------------------------------------- ###
ARG VERSION_CATCH2=v3.8.1
ENV CATCH2_SRC_PATH=${APP_ROOT}/catch2-src \
    CATCH2_BLD_PATH=${APP_ROOT}/catch2-build \
    CATCH2_INS_PATH=${APP_ROOT}/catch2

RUN set -ex && \
    git clone --branch ${VERSION_CATCH2} --depth 1 https://github.com/catchorg/Catch2.git "${CATCH2_SRC_PATH}" && \
    mkdir -p "${CATCH2_BLD_PATH}" && cd "${CATCH2_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${CATCH2_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${CATCH2_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${CATCH2_BLD_PATH}" "${CATCH2_SRC_PATH}"

ENV LD_LIBRARY_PATH="${CATCH2_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${CATCH2_INS_PATH}/lib/cmake/Catch2:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          FastJet build (autotools)                                      ###
### ---------------------------------------------------------------------- ###
ARG VERSION_FASTJET=3.4.3
ENV FASTJET_INS_PATH=${APP_ROOT}/fastjet

RUN set -ex && \
    curl -L "https://fastjet.fr/repo/fastjet-${VERSION_FASTJET}.tar.gz" | tar xz -C "${APP_ROOT}" && \
    cd "${APP_ROOT}/fastjet-${VERSION_FASTJET}" && \
    ./configure --prefix="${FASTJET_INS_PATH}" && \
    make -j"${BUILD_THREADS}" && \
    make install && \
    rm -rf "${APP_ROOT}/fastjet-${VERSION_FASTJET}"

ENV FASTJET_ROOT=${FASTJET_INS_PATH} \
    PATH="${FASTJET_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${FASTJET_INS_PATH}/lib:${LD_LIBRARY_PATH}"


### ---------------------------------------------------------------------- ###
###          HepMC3 build                                                  ###
### ---------------------------------------------------------------------- ###
ARG VERSION_HEPMC3=3.3.1
ENV HEPMC3_SRC_PATH=${APP_ROOT}/hepmc3-src \
    HEPMC3_BLD_PATH=${APP_ROOT}/hepmc3-build \
    HEPMC3_INS_PATH=${APP_ROOT}/hepmc3

RUN set -ex && \
    git clone --branch ${VERSION_HEPMC3} --depth 1 https://gitlab.cern.ch/hepmc/HepMC3.git "${HEPMC3_SRC_PATH}" && \
    mkdir -p "${HEPMC3_BLD_PATH}" && cd "${HEPMC3_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${HEPMC3_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DHEPMC3_ENABLE_PYTHON=OFF \
      "${HEPMC3_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${HEPMC3_BLD_PATH}" "${HEPMC3_SRC_PATH}"

ENV HEPMC3_DIR=${HEPMC3_INS_PATH} \
    PATH="${HEPMC3_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${HEPMC3_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${HEPMC3_INS_PATH}/share/HepMC3/cmake:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          Geant4 build                                                  ###
### ---------------------------------------------------------------------- ###
ARG VERSION_GEANT4=v11.3.0
ENV GEANT4_SRC_PATH=${APP_ROOT}/geant4-src \
    GEANT4_BLD_PATH=${APP_ROOT}/geant4-build \
    GEANT4_INS_PATH=${APP_ROOT}/geant4

RUN set -ex && \
    git clone --branch ${VERSION_GEANT4} --depth 1 https://github.com/Geant4/geant4.git "${GEANT4_SRC_PATH}" && \
    mkdir -p "${GEANT4_BLD_PATH}" && cd "${GEANT4_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${GEANT4_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DGEANT4_INSTALL_DATA=ON \
      -DGEANT4_USE_GDML=ON \
      -DGEANT4_USE_SYSTEM_CLHEP=ON \
      -DCLHEP_ROOT_DIR="${CLHEP}" \
      -DGEANT4_USE_OPENGL_X11=ON \
      -DGEANT4_USE_RAYTRACER_X11=ON \
      -DGEANT4_BUILD_MULTITHREADED=ON \
      -DGEANT4_BUILD_TLS_MODEL=global-dynamic \
      -DGEANT4_USE_QT=ON \
      -Wno-dev \
      "${GEANT4_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${GEANT4_BLD_PATH}" "${GEANT4_SRC_PATH}"

# NOTE: For runtime Geant4 data env vars, source ${GEANT4_INS_PATH}/bin/geant4.sh
ENV PATH="${GEANT4_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${GEANT4_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${GEANT4_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          PODIO build                                                   ###
### ---------------------------------------------------------------------- ###
ARG VERSION_PODIO=v01-03
ENV PODIO_SRC_PATH=${APP_ROOT}/podio-src \
    PODIO_BLD_PATH=${APP_ROOT}/podio-build \
    PODIO_INS_PATH=${APP_ROOT}/podio

RUN set -ex && \
    git clone --branch ${VERSION_PODIO} --depth 1 https://github.com/AIDASoft/podio.git "${PODIO_SRC_PATH}" && \
    mkdir -p "${PODIO_BLD_PATH}" && cd "${PODIO_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${PODIO_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DBUILD_TESTING=OFF \
      "${PODIO_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${PODIO_BLD_PATH}" "${PODIO_SRC_PATH}"

ENV PODIO_ROOT=${PODIO_INS_PATH} \
    LD_LIBRARY_PATH="${PODIO_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${PODIO_INS_PATH}/lib/cmake/podio:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          VGM build                                                     ###
### ---------------------------------------------------------------------- ###
ARG VERSION_VGM=v5-3-1
ENV VGM_SRC_PATH=${APP_ROOT}/vgm-src \
    VGM_BLD_PATH=${APP_ROOT}/vgm-build \
    VGM_INS_PATH=${APP_ROOT}/vgm

RUN set -ex && \
    git clone --branch ${VERSION_VGM} --depth 1 https://github.com/vmc-project/vgm.git "${VGM_SRC_PATH}" && \
    mkdir -p "${VGM_BLD_PATH}" && cd "${VGM_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${VGM_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${VGM_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${VGM_BLD_PATH}" "${VGM_SRC_PATH}"

ENV VGM_DIR=${VGM_INS_PATH} \
    LD_LIBRARY_PATH="${VGM_INS_PATH}/lib:${VGM_INS_PATH}/lib64:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${VGM_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          EDM4HEP build                                                 ###
### ---------------------------------------------------------------------- ###
ARG VERSION_EDM4HEP=v00-99-02
ENV EDM4HEP_SRC_PATH=${APP_ROOT}/edm4hep-src \
    EDM4HEP_BLD_PATH=${APP_ROOT}/edm4hep-build \
    EDM4HEP_INS_PATH=${APP_ROOT}/edm4hep

RUN set -ex && \
    git clone --branch ${VERSION_EDM4HEP} --depth 1 https://github.com/key4hep/EDM4hep.git "${EDM4HEP_SRC_PATH}" && \
    mkdir -p "${EDM4HEP_BLD_PATH}" && cd "${EDM4HEP_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${EDM4HEP_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DBUILD_TESTING=OFF \
      "${EDM4HEP_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${EDM4HEP_BLD_PATH}" "${EDM4HEP_SRC_PATH}"

ENV LD_LIBRARY_PATH="${EDM4HEP_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${EDM4HEP_INS_PATH}/lib/cmake/EDM4HEP:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          EDM4EIC build                                                 ###
### ---------------------------------------------------------------------- ###
ARG VERSION_EDM4EIC=v8.2.0
ENV EDM4EIC_SRC_PATH=${APP_ROOT}/edm4eic-src \
    EDM4EIC_BLD_PATH=${APP_ROOT}/edm4eic-build \
    EDM4EIC_INS_PATH=${APP_ROOT}/edm4eic

RUN set -ex && \
    git clone --branch ${VERSION_EDM4EIC} --depth 1 https://github.com/eic/edm4eic.git "${EDM4EIC_SRC_PATH}" && \
    mkdir -p "${EDM4EIC_BLD_PATH}" && cd "${EDM4EIC_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${EDM4EIC_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DBUILD_TESTING=OFF \
      "${EDM4EIC_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${EDM4EIC_BLD_PATH}" "${EDM4EIC_SRC_PATH}"

ENV LD_LIBRARY_PATH="${EDM4EIC_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${EDM4EIC_INS_PATH}/lib/EDM4EIC:${EDM4EIC_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          DD4hep build                                                  ###
### ---------------------------------------------------------------------- ###
ARG VERSION_DD4HEP=v01-31
ENV DD4HEP_SRC_PATH=${APP_ROOT}/dd4hep-src \
    DD4HEP_BLD_PATH=${APP_ROOT}/dd4hep-build \
    DD4HEP_INS_PATH=${APP_ROOT}/dd4hep

RUN set -ex && \
    git clone --branch ${VERSION_DD4HEP} --depth 1 https://github.com/AIDASoft/DD4hep.git "${DD4HEP_SRC_PATH}" && \
    mkdir -p "${DD4HEP_BLD_PATH}" && cd "${DD4HEP_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${DD4HEP_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DDD4HEP_USE_GEANT4=ON \
      -DDD4HEP_USE_XERCESC=ON \
      -DDD4HEP_USE_EDM4HEP=ON \
      -DBUILD_TESTING=OFF \
      "${DD4HEP_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${DD4HEP_BLD_PATH}" "${DD4HEP_SRC_PATH}"

ENV DD4HEP_DIR=${DD4HEP_INS_PATH} \
    PATH="${DD4HEP_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${DD4HEP_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    ROOT_INCLUDE_PATH="${DD4HEP_INS_PATH}/include:${ROOT_INCLUDE_PATH}" \
    CMAKE_PREFIX_PATH="${DD4HEP_INS_PATH}/cmake:${DD4HEP_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          ACTS build                                                    ###
### ---------------------------------------------------------------------- ###
ARG VERSION_ACTS=v41.1.0
ENV ACTS_SRC_PATH=${APP_ROOT}/acts-src \
    ACTS_BLD_PATH=${APP_ROOT}/acts-build \
    ACTS_INS_PATH=${APP_ROOT}/acts

RUN set -ex && \
    git clone --branch ${VERSION_ACTS} --depth 1 https://github.com/acts-project/acts.git "${ACTS_SRC_PATH}" && \
    mkdir -p "${ACTS_BLD_PATH}" && cd "${ACTS_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${ACTS_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DACTS_BUILD_PLUGIN_TGEO=ON \
      -DACTS_BUILD_PLUGIN_DD4HEP=ON \
      -DACTS_BUILD_PLUGIN_JSON=ON \
      -DACTS_BUILD_PLUGIN_ACTSVG=OFF \
      "${ACTS_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${ACTS_BLD_PATH}" "${ACTS_SRC_PATH}"

ENV ACTS_DIR=${ACTS_INS_PATH} \
    LD_LIBRARY_PATH="${ACTS_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${ACTS_INS_PATH}/lib/cmake/Acts:${ACTS_INS_PATH}/lib/cmake/nlohmann_json:${ACTS_INS_PATH}/lib/cmake/ActsDD4hep:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          ActsSVG build                                                 ###
### ---------------------------------------------------------------------- ###
ARG VERSION_ACTSSVG=v0.4.50
ENV ACTSSVG_SRC_PATH=${APP_ROOT}/actssvg-src \
    ACTSSVG_BLD_PATH=${APP_ROOT}/actssvg-build \
    ACTSSVG_INS_PATH=${APP_ROOT}/actssvg

RUN set -ex && \
    git clone --branch ${VERSION_ACTSSVG} --depth 1 https://github.com/acts-project/actsvg.git "${ACTSSVG_SRC_PATH}" && \
    mkdir -p "${ACTSSVG_BLD_PATH}" && cd "${ACTSSVG_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${ACTSSVG_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${ACTSSVG_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${ACTSSVG_BLD_PATH}" "${ACTSSVG_SRC_PATH}"

ENV LD_LIBRARY_PATH="${ACTSSVG_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${ACTSSVG_INS_PATH}/lib/cmake/actsvg-0.1:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          JANA2 build                                                   ###
### ---------------------------------------------------------------------- ###
ARG VERSION_JANA2=v2.4.0
ENV JANA2_SRC_PATH=${APP_ROOT}/jana2-src \
    JANA2_BLD_PATH=${APP_ROOT}/jana2-build \
    JANA2_INS_PATH=${APP_ROOT}/jana2

RUN set -ex && \
    git clone --branch ${VERSION_JANA2} --depth 1 https://github.com/JeffersonLab/JANA2.git "${JANA2_SRC_PATH}" && \
    mkdir -p "${JANA2_BLD_PATH}" && cd "${JANA2_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${JANA2_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      -DUSE_PODIO=ON \
      -DUSE_ROOT=ON \
      "${JANA2_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${JANA2_BLD_PATH}" "${JANA2_SRC_PATH}"

ENV JANA_HOME=${JANA2_INS_PATH} \
    JANA_PLUGIN_PATH="${JANA2_INS_PATH}/plugins" \
    PATH="${JANA2_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${JANA2_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${JANA2_INS_PATH}/lib/cmake/JANA:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          IRT build                                                     ###
### ---------------------------------------------------------------------- ###
ARG VERSION_IRT=v1.0.8
ENV IRT_SRC_PATH=${APP_ROOT}/irt-src \
    IRT_BLD_PATH=${APP_ROOT}/irt-build \
    IRT_INS_PATH=${APP_ROOT}/irt

RUN set -ex && \
    git clone --branch ${VERSION_IRT} --depth 1 https://github.com/eic/irt.git "${IRT_SRC_PATH}" && \
    mkdir -p "${IRT_BLD_PATH}" && cd "${IRT_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${IRT_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${IRT_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${IRT_BLD_PATH}" "${IRT_SRC_PATH}"

ENV LD_LIBRARY_PATH="${IRT_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${IRT_INS_PATH}/lib/cmake/IRT:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          NPDet build                                                   ###
### ---------------------------------------------------------------------- ###
ARG VERSION_NPDET=v1.4.1
ENV NPDET_SRC_PATH=${APP_ROOT}/npdet-src \
    NPDET_BLD_PATH=${APP_ROOT}/npdet-build \
    NPDET_INS_PATH=${APP_ROOT}/npdet

RUN set -ex && \
    git clone --branch ${VERSION_NPDET} --depth 1 https://eicweb.phy.anl.gov/EIC/NPDet.git "${NPDET_SRC_PATH}" && \
    mkdir -p "${NPDET_BLD_PATH}" && cd "${NPDET_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${NPDET_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${NPDET_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${NPDET_BLD_PATH}" "${NPDET_SRC_PATH}"

ENV PATH="${NPDET_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${NPDET_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${NPDET_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          Algorithms build                                              ###
### ---------------------------------------------------------------------- ###
ARG VERSION_ALGORITHMS=v1.0.0
ENV ALGORITHMS_SRC_PATH=${APP_ROOT}/algorithms-src \
    ALGORITHMS_BLD_PATH=${APP_ROOT}/algorithms-build \
    ALGORITHMS_INS_PATH=${APP_ROOT}/algorithms

RUN set -ex && \
    git clone --branch ${VERSION_ALGORITHMS} --depth 1 https://github.com/eic/algorithms.git "${ALGORITHMS_SRC_PATH}" && \
    mkdir -p "${ALGORITHMS_BLD_PATH}" && cd "${ALGORITHMS_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${ALGORITHMS_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${ALGORITHMS_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${ALGORITHMS_BLD_PATH}" "${ALGORITHMS_SRC_PATH}"

ENV LD_LIBRARY_PATH="${ALGORITHMS_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${ALGORITHMS_INS_PATH}:${CMAKE_PREFIX_PATH}"


### ---------------------------------------------------------------------- ###
###          JANA4ML4FPGA build                                            ###
### ---------------------------------------------------------------------- ###
ARG VERSION_JANA4ML4FPGA=main
ENV JANA4ML4FPGA_SRC_PATH=${APP_ROOT}/jana4ml4fpga-src \
    JANA4ML4FPGA_BLD_PATH=${APP_ROOT}/jana4ml4fpga-build \
    JANA4ML4FPGA_INS_PATH=${APP_ROOT}/jana4ml4fpga

RUN set -ex && \
    git clone --branch ${VERSION_JANA4ML4FPGA} --depth 1 https://github.com/JeffersonLab/JANA4ML4FPGA.git "${JANA4ML4FPGA_SRC_PATH}" && \
    mkdir -p "${JANA4ML4FPGA_BLD_PATH}" && cd "${JANA4ML4FPGA_BLD_PATH}" && \
    cmake \
      -DCMAKE_INSTALL_PREFIX="${JANA4ML4FPGA_INS_PATH}" \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_STANDARD=${CXX_STANDARD} \
      "${JANA4ML4FPGA_SRC_PATH}" && \
    cmake --build . --target install -j"${BUILD_THREADS}" && \
    rm -rf "${JANA4ML4FPGA_BLD_PATH}" "${JANA4ML4FPGA_SRC_PATH}"

ENV JANA_PLUGIN_PATH="${JANA4ML4FPGA_INS_PATH}/plugins:${JANA_PLUGIN_PATH}" \
    PATH="${JANA4ML4FPGA_INS_PATH}/bin:${PATH}" \
    LD_LIBRARY_PATH="${JANA4ML4FPGA_INS_PATH}/lib:${LD_LIBRARY_PATH}" \
    CMAKE_PREFIX_PATH="${JANA4ML4FPGA_INS_PATH}:${CMAKE_PREFIX_PATH}"


SHELL ["/bin/bash", "-c"]
