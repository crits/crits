FROM ubuntu:latest

MAINTAINER crits

RUN apt-get -qq update
# git command
RUN apt-get install -y git
# pip command
RUN apt-get install -y python-pip
# lsb_release command
RUN apt-get install -y lsb-release 
# sudo command
RUN apt-get install -y sudo
# add-apt-repository command
RUN apt-get install -y software-properties-common

RUN git clone --depth 1 https://github.com/crits/crits.git 

WORKDIR crits
RUN TERM=xterm sh script/bootstrap < docker_inputs

EXPOSE 8080

CMD sh contrib/mongo/mongod_start.sh && python manage.py runserver 0.0.0.0:8080
