FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get upgrade -y && \
    pip install poetry

WORKDIR /app

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY muell muell
COPY database.ini database.ini

RUN poetry install

CMD [ "poetry", "run", "trash-dates", "--schedule"]
