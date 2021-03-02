FROM python:3.9

# Cargo cult
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.0.5

WORKDIR /app
COPY . .

RUN pip install "poetry==$POETRY_VERSION"
RUN poetry install --no-dev

ENTRYPOINT ["poetry", "run", "./hardplacepro/__main__.py"]
