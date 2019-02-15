FROM python:3

ADD starterbot.py /
ADD trigger.sh /

RUN pip install slackclient
RUN pip install prometheus_client

CMD [ "python", "./starterbot.py" ]
