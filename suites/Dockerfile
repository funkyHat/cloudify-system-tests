FROM ubuntu:12.04

RUN apt-get update
RUN apt-get -f install -y
RUN apt-get install -y python python-dev python-pip curl wget git
RUN pip install pip --upgrade
RUN pip install virtualenv

ENV HOME /root