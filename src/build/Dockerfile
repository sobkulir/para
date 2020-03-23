FROM ubuntu:16.04

ARG requirements

RUN apt-get update && \
    apt-get upgrade -y

# Python 3.6:
RUN DEBIAN_FRONTEND=noninteractive apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install python3.6 python3.6-dev python3.6-venv -y

# Add missing file libGL.so.1 for PyQt5.QtGui:
RUN apt-get install libgl1-mesa-glx -y

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get update && apt-get install -y --no-install-recommends apt-utils \
    python3-pip && \
    apt-get install -y git && \
    apt-get install -y ruby ruby-dev rubygems build-essential && \
    apt-get install -y python3-setuptools

# fpm:
RUN apt-get install ruby ruby-dev build-essential -y && \
    gem install --no-ri --no-rdoc fpm

RUN git clone https://github.com/sobkulir/para

WORKDIR /para

# Set up virtual environment:
RUN python3.6 -m venv venv && \
    . venv/bin/activate && \
    venv/bin/python -m pip install -r requirements.txt

RUN . venv/bin/activate && \
    fbs freeze && \
    fbs installer
