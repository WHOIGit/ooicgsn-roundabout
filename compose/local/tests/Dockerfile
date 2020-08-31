FROM ubuntu:18.04
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get install curl -y
# Tools for Circleci debugging
RUN apt-get install iputils-ping -y && apt-get install net-tools -y

RUN apt-get install -y wget && apt install -y unzip

# At Circleci root dir
COPY ./tests /tests

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get install -y nodejs
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb              
RUN wget https://chromedriver.storage.googleapis.com/84.0.4147.30/chromedriver_linux64.zip && unzip -o chromedriver_linux64.zip -d/usr/local/bin
RUN apt remove firefox && apt remove firefox-geckodriver
RUN apt install -y firefox && apt install -y firefox-geckodriver

RUN chmod +x /tests/RunAllTests-Chrome-Linux.bat
RUN sed -i 's/\r//' /tests/RunAllTests-Chrome-Linux.bat

RUN chmod +x /tests/RunAllTests-Firefox-Linux.bat
RUN sed -i 's/\r//' /tests/RunAllTests-Firefox-Linux.bat

WORKDIR /tests

