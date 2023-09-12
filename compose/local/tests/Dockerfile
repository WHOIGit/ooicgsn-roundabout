FROM ubuntu:latest

# Required for nodejs 15+
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
# Need to remove it
RUN apt remove -y nodejs
RUN apt remove -y nodejs-doc
RUN apt-get -y autoremove
# Selenium Webdriver version 4.8.0 requires node 14 or higher
#RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - 
#RUN apt-get install -y nodejs
# Above node install is depreciated with a 60 second wait
RUN apt-get update && apt-get install -y ca-certificates curl gnupg
RUN mkdir -p /etc/apt/keyrings  
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
     | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_16.x nodistro main" \
     | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update
RUN apt-get install nodejs -y

# npm WARN EBADENGINE package: 'jsdom@20.0.0' with Node 12.x
RUN npm install jsdom@19.0.0
RUN npm install jquery
RUN npm install jquery-csv
RUN npm install unzipper
# node-fetch v3 errors with require(), needs import
RUN npm install node-fetch@2.6.1
# Needed for "Chrome for Testing"
RUN apt-get -y install jq
RUN apt-get -y install default-jre
RUN apt-get -f install
RUN apt-get update && apt-get install -y libxkbcommon0  libpangocairo-1.0 libxdamage1 libgbm1

RUN npm install selenium-webdriver

#RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && apt install -y ./google-chrome-stable_current_amd64.deb      
# Get Chrome for Testing - Chrome stable version number does not match the Chrome for Testing stable version
RUN CHROME_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chrome[] | select(.platform == "linux64") | .url') \
    && curl -sSLf --retry 3 --output /tmp/chrome-linux64.zip "$CHROME_URL" \
    && unzip /tmp/chrome-linux64.zip -d /opt \
    && ln -s /opt/chrome-linux64/chrome /usr/local/bin/chrome \
    && rm /tmp/chrome-linux64.zip

# Get Chromedriver for Testing - this is the only supported version going forward
#RUN CHROME_VERSION=$(google-chrome --version | sed -n 's/Google Chrome \([0-9.]*\).*/\1/p; s/[^0-9.]//g') \
#  && wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROME_VERSION/linux64/chromedriver-linux64.zip \
#  && unzip -o chromedriver-linux64.zip -d /usr/local/bin
RUN CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform == "linux64") | .url') \
    && curl -sSLf --retry 3 --output /tmp/chromedriver-linux64.zip "$CHROMEDRIVER_URL" \
    && unzip -o /tmp/chromedriver-linux64.zip -d /tmp \
    && rm -rf /tmp/chromedriver-linux64.zip \
    && mv -f /tmp/chromedriver-linux64/chromedriver "/usr/local/bin/chromedriver" \
    && chmod +x "/usr/local/bin/chromedriver"
        
RUN chmod +x /tests/RunAllTests-Chrome-Linux.bat
RUN sed -i 's/\r//' /tests/RunAllTests-Chrome-Linux.bat

RUN chmod +x /tests/Cleanup-Docker.bat
RUN sed -i 's/\r//' /tests/Cleanup-Docker.bat

RUN chmod +x /tests/Buildup-Docker.bat
RUN sed -i 's/\r//' /tests/Buildup-Docker.bat



