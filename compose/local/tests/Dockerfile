FROM ubuntu:18.04

# Install nodejs
RUN apt-get update &&\
    apt-get -y install curl &&\
    curl -sL https://deb.nodesource.com/setup_10.x &&\
    apt-get -y install nodejs

RUN node -v

RUN apt-get install -y wget && apt install -y unzip

# For Circleci
COPY ./tests /tests
# For command line testing
#COPY . /tests

WORKDIR /tests

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb
RUN wget https://chromedriver.storage.googleapis.com/84.0.4147.30/chromedriver_linux64.zip && unzip -d /tests chromedriver_linux64.zip
RUN apt install -y firefox && apt install -y firefox-geckodriver

RUN chromedriver -v
RUN firefox -v
RUN geckodriver -v

RUN chmod +x RunAllTests-Chrome-Linux.bat
RUN sed -i 's/\r//' RunAllTests-Chrome-Linux.bat

RUN chmod +x RunAllTests-Firefox-Linux.bat
RUN sed -i 's/\r//' RunAllTests-Firefox-Linux.bat

