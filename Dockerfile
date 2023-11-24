FROM ghcr.io/osgeo/gdal:ubuntu-small-3.3.0-arm64
ARG DEVEL

# CREATE SOME DIRECTORIES
RUN mkdir /in
RUN mkdir /out
RUN mkdir /src

# Install pip
RUN apt update
RUN apt install -y python3-pip

# install some additional packages
RUN pip install click

# This is only for development
RUN pip install ipython


# copy over all the files
COPY ./src /src

WORKDIR /src
CMD ["python", "/src/compress.py"]
