FROM python:3.8.3

EXPOSE 5000

WORKDIR /home/project

COPY . .

RUN pip3 install -r ./requirements.txt

CMD gunicorn --bind :5000 -w 4 api:app
