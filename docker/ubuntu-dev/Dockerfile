#
# docker build -t eicdev/ubuntu-dev:latest .
# docker build -t eicdev/ubuntu-dev:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/ubuntu-dev:latest
#
# docker run --rm -it --init eicdev/ubuntu-dev:latest
# docker run --rm -it --init -p8888:8888 eicdev/ubuntu-dev:latest

FROM ubuntu:noble

# Number of build threads
ARG BUILD_THREADS=8

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


