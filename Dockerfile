FROM ubuntu:xenial

RUN apt-get update
RUN apt-get install -y curl git build-essential make
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y python python-pip
RUN npm install -g yarn
RUN apt-get install -y redis-server

COPY . /HookCatcher
WORKDIR /HookCatcher

RUN pip install -r requirements.txt
RUN yarn install
