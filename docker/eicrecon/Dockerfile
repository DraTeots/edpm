#
# docker build -t eicdev/full-stack-prereq:latest .
# docker build -t eicdev/full-stack-prereq:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/full-stack-prereq:latest
# 
# docker run --rm -it --init eicdev/full-stack-prereq:latest
# docker run --rm -it --init -p8888:8888 eicdev/full-stack-prereq:latest

FROM eicdev/ubuntu-dev:latest

# Number of build threads
ARG BUILD_THREADS=8

ENV EIC_ROOT /eic
ENV CONTAINER_ROOT /container
ENV APP_ROOT /container/app

SHELL ["/bin/bash", "-c"]

ARG DEBIAN_FRONTEND=noninteractive


RUN useradd -m -G sudo eicuser
RUN echo "eicuser ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

RUN install -d -o eicuser -g eicuser ${CONTAINER_ROOT} && \
    install -d -o eicuser -g eicuser ${APP_ROOT} && \
    install -d -o eicuser -g eicuser /eic

USER eicuser
WORKDIR /home/eicuser
ENV PATH "$PATH:/home/eicuser/.local/bin"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8


RUN python3 -m pip install --user --upgrade --force-reinstall  click &&\
    python3 -m pip install --user --upgrade --force-reinstall  appdirs &&\
    python3 -m pip install --user --upgrade --force-reinstall  edpm &&\
    edpm --top-dir=/container/app &&\
    edpm


# THIS IS NOT WORKING! HuCK debconf
# # https://github.com/moby/moby/issues/27988
# 
# # install all packets but not eicrecon
# RUN  sudo apt-get update &&\
#      echo $(edpm req --all ubuntu) &&\     
#      sudo echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections &&\
#      sudo chmod 777 /var/cache/debconf/ &&\
#      sudo chmod 777 /var/cache/debconf/passwords.dat &&\
#      sudo apt-get -y -q install $(edpm req --all ubuntu) &&\
#      sudo rm -rf /var/lib/apt/lists/*
# (!) Build with C++20
# eicrecon stack
RUN edpm config global cxx_standard=17 &&\
    edpm install clhep && edpm clean clhep &&\
    edpm install eigen3 && edpm clean eigen3

RUN edpm config root branch="v6-28-00" &&\
    edpm config root cmake_custom_flags="-Droofit=OFF" &&\
    edpm install -j${BUILD_THREADS} root && edpm clean root &&\
    edpm install hepmc3 && edpm clean hepmc3 &&\
    edpm install -j${BUILD_THREADS} geant4 && edpm clean geant4


# aa
RUN python3 -m pip install --user --upgrade --force-reinstall  edpm &&\
    edpm install eicrecon --deps-only 

# jupyterab
RUN python3 -m pip install jupyterlab

ADD test_jsroot.ipynb /home/eicuser/

RUN echo "done"

CMD jupyter lab --ip=0.0.0.0 --no-browser \
    --NotebookApp.custom_display_url=http://127.0.0.1:8888 \
    --NotebookApp.token=''