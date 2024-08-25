FROM python:3.9

# install google chrome
# Reference: https://stackoverflow.com/questions/70955307/how-to-install-google-chrome-in-a-docker-container
RUN apt-get install -y wget
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/`curl -sS https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE`/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /usr/local/bin/
RUN mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
# set display port to avoid crash
ENV DISPLAY=:99

# Install requirements first so this step is cached by Docker
COPY /requirements.txt /home/project/requirements.txt
WORKDIR /home/project/
RUN pip install -r requirements.txt

# copy code
COPY /main.py /home/project/

CMD ["python", "./main.py"]
