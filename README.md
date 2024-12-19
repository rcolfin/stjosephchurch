# stjoseph

[![CI Build](https://github.com/rcolfin/stjosephchurch/actions/workflows/ci.yml/badge.svg)](https://github.com/stjosephchurch/python/actions/workflows/ci.yml)

Package to set up and manage the Live Stream for [Saint Joseph Church Lincoln Park NJ](https://www.youtube.com/@saintjosephchurchlincolnpa905)

It relies on the [YouTube Data API v3](https://developers.google.com/youtube/v3) to interact with the YouTube Channel.

## Development

### Setup Python Environment:

Run [scripts/console.sh](../scripts/console.sh) poetry install

### If you need to relock:

Run [scripts/lock.sh](../scripts/lock.sh)

### Run code

Run [scripts/console.sh](../scripts/console.sh) poetry run python -m stjoseph


## API Usage:

As a CLI

To schedule a mass:

```sh
python -m stjoseph schedule-mass '2024-12-21 17:30' --public
```

To schedule masses a month in advance:

```sh
python -m stjoseph schedule-masses --public
```