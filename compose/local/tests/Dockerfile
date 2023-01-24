FROM ubuntu:latest

# Required for nodejs 15+ and npm - needs to go here
WORKDIR /tests

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update

RUN apt-get install curl -y && apt-get install npm -y

RUN apt-get install -y wget && apt install -y unzip

# At root dir
COPY ./tests/*.bat /tests/
COPY ./tests/*.js /tests/
COPY ./tests/*.csv /tests/
COPY ./tests/*.ext /tests/

# The default Ubuntu 22.04 repository contains an old version 12.22.9 of Node.js
# To install Node.js from default repositories, run:
# RUN apt-get install -y nodejs
# But, Selenium Webdriver version 4.8.0 requires node 14 or higher
RUN apt remove nodejs
RUN apt remove nodejs-doc
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - 
RUN apt-get install -y nodejs

# npm WARN EBADENGINE package: 'jsdom@20.0.0' with Node 12.x
RUN npm install jsdom@19.0.0
RUN npm install jquery
RUN npm install jquery-csv
RUN npm install unzipper
# node-fetch v3 errors with require(), needs import
RUN npm install node-fetch@2.6.1

RUN npm install selenium-webdriver

# Prevents unable to fetch archive.ubuntu.com google chrome error below
RUN apt-get update

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb      

# Determine and Get Chromedriver Version based upon the Google Chrome Version
RUN CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome \([0-9]*\).*/\1/g') \
  && CHROME_DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) \
  && wget https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
  && unzip -o chromedriver_linux64.zip -d/usr/local/bin
        
RUN chmod +x /tests/RunAllTests-Chrome-Linux.bat
RUN sed -i 's/\r//' /tests/RunAllTests-Chrome-Linux.bat

RUN chmod +x /tests/Cleanup-Docker.bat
RUN sed -i 's/\r//' /tests/Cleanup-Docker.bat

RUN chmod +x /tests/Buildup-Docker.bat
RUN sed -i 's/\r//' /tests/Buildup-Docker.bat

#RUN chmod +x /tests/RunAllTests-Firefox-Linux.bat
#RUN sed -i 's/\r//' /tests/RunAllTests-Firefox-Linux.bat



