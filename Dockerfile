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

# Clone the repo
RUN git clone --depth 1 https://github.com/crits/crits.git 

WORKDIR crits
# Install the dependencies
RUN TERM=xterm sh ./script/bootstrap < docker_inputs

# Create a new admin. Username: "admin" , Password: "pass1PASS123!"
RUN sh contrib/mongo/mongod_start.sh && python manage.py users -u admin -p "pass1PASS123!" -s -i -a -A -e admin@crits.crits -f "first" -l "last" -o "no-org"

EXPOSE 8080

CMD sh contrib/mongo/mongod_start.sh && python manage.py runserver 0.0.0.0:8080
