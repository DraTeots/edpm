#
# docker build -t eicdev/full-stack:latest .
# docker build -t eicdev/full-stack:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/full-stack:latest
#
# docker run --rm -it --init eicdev/full-stack:latest
# docker run --rm -it --init -p8888:8888 eicdev/full-stack:latest

FROM eicdev/ubuntu-dev:latest

# Number of build threads
ARG BUILD_THREADS=8

ENV EIC_ROOT /eic
ENV CONTAINER_ROOT /container
ENV APP_ROOT /container/app

SHELL ["/bin/bash", "-c"]

ARG DEBIAN_FRONTEND=noninteractive

# Setup user and directories
RUN useradd -m -G sudo eicuser && \
    echo "eicuser ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers && \
    install -d -o eicuser -g eicuser ${CONTAINER_ROOT} && \
    install -d -o eicuser -g eicuser ${APP_ROOT} && \
    install -d -o eicuser -g eicuser /eic

USER eicuser
WORKDIR /home/eicuser
ENV PATH "$PATH:/home/eicuser/.local/bin"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install EDPM
RUN python3 -m pip install --user --upgrade pip && \
    python3 -m pip install --user --upgrade click appdirs && \
    python3 -m pip install --user --upgrade edpm && \
    edpm --top-dir=/container/app

# Initialize EDPM plan file
RUN edpm init

# Install OS dependencies for all packages
RUN sudo apt-get update && \
    sudo apt-get install -y $(edpm req ubuntu --all) && \
    sudo rm -rf /var/lib/apt/lists/*

# Set global configuration
RUN edpm config global cxx_standard=17

# ========== Foundation Libraries ==========

# CLHEP
RUN edpm add clhep && \
    edpm install clhep  && \
    edpm clean clhep

# Eigen3
RUN edpm add eigen3 && \
    edpm install eigen3  && \
    edpm clean eigen3

# Catch2
RUN edpm add catch2 && \
    edpm install catch2  && \
    edpm clean catch2

# Fastjet
RUN edpm add fastjet && \
    edpm install fastjet  && \
    edpm clean fastjet

# ========== Mid-level Dependencies ==========

# ROOT
RUN edpm add root@v6-34-04 && \
    edpm install root  && \
    edpm clean root

# HepMC3
RUN edpm add hepmc3 && \
    edpm install hepmc3  && \
    edpm clean hepmc3

# Geant4
RUN edpm add geant4 && \
    edpm install geant4  && \
    edpm clean geant4

# PODIO
RUN edpm add podio && \
    edpm install podio  && \
    edpm clean podio

# VGM
RUN edpm add vgm && \
    edpm install vgm  && \
    edpm clean vgm

# ========== Higher-level Frameworks ==========

# EDM4HEP
RUN edpm add edm4hep && \
    edpm install edm4hep  && \
    edpm clean edm4hep

# EDM4EIC
RUN edpm add edm4eic && \
    edpm install edm4eic  && \
    edpm clean edm4eic

# DD4HEP
RUN edpm add dd4hep && \
    edpm install dd4hep  && \
    edpm clean dd4hep

# ACTS
RUN edpm add acts && \
    edpm install acts  && \
    edpm clean acts

# ACTSSVG
RUN edpm add actssvg && \
    edpm install actssvg  && \
    edpm clean actssvg

# JANA2
RUN edpm add jana2 && \
    edpm install jana2  && \
    edpm clean jana2

# IRT
RUN edpm add irt && \
    edpm install irt  && \
    edpm clean irt

# NPDet
RUN edpm add npdet && \
    edpm install npdet  && \
    edpm clean npdet

# ========== Top-level Applications ==========

# Algorithms
RUN edpm add algorithms && \
    edpm install algorithms  && \
    edpm clean algorithms

# JANA4ML4FPGA
RUN edpm add jana4ml4fpga && \
    edpm install jana4ml4fpga  && \
    edpm clean jana4ml4fpga

# EPIC
RUN edpm add epic && \
    edpm install epic  && \
    edpm clean epic

# EICRecon dependencies
RUN edpm add eicrecon --option deps_only=true && \
    edpm install eicrecon --deps-only 

# Install JupyterLab
RUN python3 -m pip install --user jupyterlab

# Add test notebook
ADD test_jsroot.ipynb /home/eicuser/

RUN echo "EDPMv3 build completed"

CMD jupyter lab --ip=0.0.0.0 --no-browser \
    --NotebookApp.custom_display_url=http://127.0.0.1:8888 \
    --NotebookApp.token=''