FROM ubuntu:18.04

RUN apt-get update && apt-get install -y python3-pip

COPY /requirements.txt /
RUN pip3 install --disable-pip-version-check -r /requirements.txt

COPY source/ hwhelper/

CMD cd /hwhelper && python3 main.py
