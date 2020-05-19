FROM python:3.7

RUN python -m pip install --upgrade pip
WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_ENV development
ENV TOKEN_KEY
COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

COPY . /code
CMD ["flask", "run"]
