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
RUN poetry export --without-hashes -f requirements.txt | pip install -r /dev/stdin

ENTRYPOINT ["python3", "./hardplacepro/__main__.py"]
