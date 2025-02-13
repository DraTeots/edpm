#
# docker build -t eicdev/eicrecon-ubuntu22:latest .  
# docker build -t eicdev/eicrecon-ubuntu22:latest --build-arg BUILD_THREADS=24 .
# docker push eicdev/eicrecon-ubuntu22:latest
# 
# docker run --rm -it --init eicdev/eicrecon-ubuntu22-prereq:latest
# docker run --rm -it --init -p8888:8888 eicdev/eicrecon-ubuntu22-prereq:latest

FROM eicdev/eicrecon-ubuntu22-prereq:latest

# aaa
RUN python3 -m pip install --user --upgrade --force-reinstall  edpm &&\
    edpm install eicrecon

# jupyterab
RUN echo "done"

CMD jupyter lab --ip=0.0.0.0 --no-browser \
    --NotebookApp.custom_display_url=http://127.0.0.1:8888 \
    --NotebookApp.token=''