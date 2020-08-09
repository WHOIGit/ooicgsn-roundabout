FROM ubuntu:18.04
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils

WORKDIR /tests

RUN apt-get install -y nodejs && apt install -y npm
RUN apt-get install -y wget && apt install -y unzip

# For Circleci
COPY /tests /tests

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb
RUN wget https://chromedriver.storage.googleapis.com/84.0.4147.30/chromedriver_linux64.zip && unzip -d /tests chromedriver_linux64.zip
RUN apt install -y firefox && apt install -y firefox-geckodriver

RUN chmod +x RunAllTests-Chrome-Linux.bat
RUN sed -i 's/\r//' RunAllTests-Chrome-Linux.bat

RUN chmod +x RunAllTests-Firefox-Linux.bat
RUN sed -i 's/\r//' RunAllTests-Firefox-Linux.bat

