FROM ubuntu:16.04

ARG requirements

RUN apt-get update && \
    apt-get upgrade -y

# Python 3.6:
RUN DEBIAN_FRONTEND=noninteractive apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install python3.6 python3.6-dev python3.6-venv python3-setuptools -y


# Add missing file libGL.so.1 for PyQt5.QtGui:
RUN apt-get install libgl1-mesa-glx -y

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends apt-utils \
    python3-pip && \
    apt-get install -y git

# fpm:
RUN apt-get install ruby ruby-dev build-essential -y && \
    gem install --no-ri --no-rdoc fpm

# Hot fix
RUN apt-get install -y wget && \
    wget https://www.zlib.net/fossils/zlib-1.2.9.tar.gz
RUN tar -xvf zlib-1.2.9.tar.gz
RUN cd zlib-1.2.9 && \
    ./configure && \
    make && \
    make install

RUN cd /lib/x86_64-linux-gnu && \
    ln -s -f /usr/local/lib/libz.so.1.2.9/lib libz.so.1
WORKDIR /root/${app_name}

# Set up virtual environment:
ADD *.txt /tmp/requirements/
RUN ls /tmp/requirements
RUN python3.6 -m venv venv && \
    venv/bin/python -m pip install -r "/tmp/requirements/${requirements}"
RUN rm -rf /tmp/requirements/

# Welcome message, displayed by ~/.bashrc:
# ADD motd /etc/motd

# ADD .bashrc /root/.bashrc
