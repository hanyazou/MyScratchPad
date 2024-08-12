FROM ubuntu:22.04

ARG USER=user
ARG GROUP=users
ARG UID=1000
ARG GID=1000
ARG PASSWORD=user
ARG GOWIN=Gowin_V1.9.9Beta-4_Education

RUN set -eux; \
  apt update; \
  apt install -y \
    libglib2.0-0 sudo build-essential xkb-data libdbus-1-3 libusb-dev locales

RUN set -eux; \
    ln -sf /bin/bash /bin/sh && \
    locale-gen en_US.UTF-8

RUN (groupadd -g $GID $GROUP || groupmod -g $GID $GROUP || true) && \
    useradd -m -s /bin/bash -u $UID -g $GID -G sudo $USER && \
    echo $USER:$PASSWORD | chpasswd && \
    echo "$USER   ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ADD $GOWIN.tar.gz /usr/local/bin/gowin
RUN set -eux; \
    cd /usr/local/bin/gowin && \
    mv ./IDE/lib/libfreetype.so.6 ./IDE/lib/libfreetype.so.6.BACKUP

ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV PATH /usr/local/bin/gowin/IDE/bin:/usr/local/bin/gowin/Programmer/bin:$PATH

USER $USER
WORKDIR /home/$USER/

RUN set -eux; \
    echo "PS1='\\w\\$ '" >> ~/.bashrc
