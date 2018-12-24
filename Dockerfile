FROM python:3

ADD starterbot.py /
ADD trigger.sh /

RUN pip install slackclient

CMD [ "python", "./starterbot.py" ]
