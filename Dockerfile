FROM ghcr.io/osgeo/gdal:ubuntu-small-3.3.0
ARG DEVEL

# CREATE SOME DIRECTORIES
RUN mkdir /input
RUN mkdir /output
RUN mkdir /src

# Install pip
RUN apt update
RUN apt install -y python3-pip

# install some additional packages
RUN pip install tqdm

# This is only for development
RUN if [[ -n "$DEVEL" ]]; then pip install ipython; fi


# copy over all the files
COPY ./src /src

CMD ["python", "/src/main.py"]
