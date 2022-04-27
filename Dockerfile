FROM python:3.10-slim-buster

RUN apt-get update && \
    apt-get upgrade -y && \
    pip install poetry

WORKDIR /app

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY muell muell

RUN poetry install

CMD [ "poetry", "run", "hypercorn", "-b", "0.0.0.0:5000", "muell.main:app"]
