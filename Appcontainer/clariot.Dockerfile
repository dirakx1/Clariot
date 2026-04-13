FROM debian:stretch

MAINTAINER clariot team

## CONFIGURE LOCALES
RUN apt-get update && apt-get install -y locales && \
	sed -i 's%^# en_US.UTF-8 UTF-8$%en_US.UTF-8 UTF-8%' /etc/locale.gen && \
	locale-gen
ENV LANG en_US.UTF-8

## UPDATE REPOSITORIES, INSTALL PIP AND BUILD DEPENDENCIES 
RUN apt-get update 

ENV GITPROJECT clariot-test  # GIT repo of flask microservice.

## INSTALL requirements.txt


## SINCE WE DO NOT USE GUNICORN

## REMOVE UNEEDED PACKAGES
RUN apt-mark manual libpq5 && \
	apt-get remove -y libjpeg62-turbo-dev zlib1g-dev python3.5-dev libldap2-dev libsasl2-dev libpq-dev pandoc git wget libpcre3-dev && \
	apt-get autoremove -y

## CREATE A SPACE TO MOUNT DATA AND MOVE TO IT
RUN mkdir /app
WORKDIR /app

## DO NOT RUN CELERY / UWSGI AS ROOT
RUN groupadd -g 1000 -r flask && useradd -r -u 1000 -g flask flask
RUN mkdir /home/flask && chown flask: /home/flask
USER flask
#ENTRYPOINT ["clariot-entrypoint.sh"]
