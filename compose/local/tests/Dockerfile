FROM ubuntu:latest

# Required here for nodejs 15+ and npm - needs to go here
WORKDIR /tests

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update

RUN apt-get install curl -y && apt-get install npm -y
# Tools for Circleci debugging
RUN apt-get install iputils-ping -y && apt-get install net-tools -y

RUN apt-get install -y wget && apt install -y unzip

# At Circleci root dir
COPY ./tests/*.bat /tests/
COPY ./tests/*.js /tests/
COPY ./tests/*.csv /tests/
COPY ./tests/*.ext /tests/

#RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
#RUN apt-get install -y nodejs
#nodesource not yet supported for ubuntu jammy rls 22.04 - 4/25/2022, issue #1379
RUN curl -LO https://nodejs.org/dist/v18.0.0/node-v18.0.0-linux-x64.tar.xz
RUN tar -xvf node-v18.0.0-linux-x64.tar.xz

RUN npm install jsdom
RUN npm install jquery
RUN npm install jquery-csv
RUN npm install unzipper
# node-fetch v3 errors with require(), needs import
RUN npm install node-fetch@2.6.1

RUN npm install selenium-webdriver

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb              
RUN wget https://chromedriver.storage.googleapis.com/101.0.4951.41/chromedriver_linux64.zip && unzip -o chromedriver_linux64.zip -d/usr/local/bin

#RUN apt install -y firefox && apt install -y firefox-geckodriver

RUN chmod +x /tests/RunAllTests-Chrome-Linux.bat
RUN sed -i 's/\r//' /tests/RunAllTests-Chrome-Linux.bat

RUN chmod +x /tests/Cleanup-Docker.bat
RUN sed -i 's/\r//' /tests/Cleanup-Docker.bat

RUN chmod +x /tests/Buildup-Docker.bat
RUN sed -i 's/\r//' /tests/Buildup-Docker.bat

#RUN chmod +x /tests/RunAllTests-Firefox-Linux.bat
#RUN sed -i 's/\r//' /tests/RunAllTests-Firefox-Linux.bat



