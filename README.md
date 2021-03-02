# hardplacepro

Track Planet Granite climbing reservations.

## Develop

```
pip install poetry
poetry install
poetry run ./hardplacepro/__main__.py
```

## Package

```
make docker
```

## Run

```
docker run -t hardplacepro:latest tomorrow
docker run -t hardplacepro:latest thursday
```

## Overengineered?

Yes.

## LICENSE

WTFPL
