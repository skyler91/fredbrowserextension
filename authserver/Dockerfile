FROM python:3.7-stretch

RUN apt-get update -y
RUN apt-get install -y python-pip
#RUN apt-get install -y python-dev build-essential

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY app ./
ENV GOOGLE_APPLICATION_CREDENTIALS $APP_HOME/key.json

RUN pip install --upgrade Flask firebase_admin requests py-bcrypt

#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
ENTRYPOINT ["python"]
CMD ["app.py"]
