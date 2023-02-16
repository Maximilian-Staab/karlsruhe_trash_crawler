FROM python:3.10-slim-buster as base
ENTRYPOINT ["tini", "--"]

ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
	BUILD_PATH="/build" \
	VENV_PATH="/build/.venv"


# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update && \
    apt-get upgrade -y && \
	apt-get install -y tini


FROM base as build
RUN pip install poetry

WORKDIR $BUILD_PATH

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN poetry install


FROM base as runtime

COPY --from=build $BUILD_PATH $BUILD_PATH
COPY ./muell /app/muell
WORKDIR /app

CMD [ "hypercorn", "-b", "0.0.0.0:5000", "muell.main:app" ]
