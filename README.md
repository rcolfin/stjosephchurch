# stjosephchurch

[![CI Build](https://github.com/rcolfin/stjosephchurch/actions/workflows/ci.yml/badge.svg)](https://github.com/stjosephchurch/python/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/rcolfin/stjosephchurch.svg)](https://github.com/rcolfin/stjosephchurch/blob/main/LICENSE)

Package to set up and manage the Live Stream for [Saint Joseph Church Lincoln Park NJ](https://www.youtube.com/@saintjosephchurchlincolnpa905)

To reduce the manual steps involved with setting up a Scheduled Live Stream which includes the [Readings](https://bible.usccb.org/bible/readings/), I came up with this app to sources the Readings from [catholic-mass-readings](https://github.com/rcolfin/catholic-mass-readings) package, then utilizing the [YouTube Data API v3](https://developers.google.com/youtube/v3) to insert (or update) the masses on the YouTube Channel.  Through the CLI below, I can schedule the masses for the entire year (only what is available via the [Readings](https://bible.usccb.org/bible/readings/) website) within a matter of seconds.


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

To schedule the Christ Pageant mass:

(Schedules the mass on Christmas Eve at 4:30 PM using the Readings for the [Christmas Mass during the Night](https://bible.usccb.org/bible/readings/122524-Night.cfm).)

```sh
python -m stjoseph schedule-mass '2024-12-24 16:00' --mass-date '2024-12-25' --schedule-end '2024-12-24 16:30' --public --type night
```

or through the launcher...

```sh
scripts/launch.sh schedule-mass '2024-12-21 17:30' --public
```

To schedule masses a month in advance:

```sh
scripts/launch.sh schedule-masses --public
```

To schedule the Christ Pageant mass:

(Schedules the mass on Christmas Eve at 4:30 PM using the Readings for the [Christmas Mass during the Night](https://bible.usccb.org/bible/readings/122524-Night.cfm).)

```sh
scripts/launch.sh schedule-mass '2024-12-24 16:00' --mass-date '2024-12-25' --schedule-end '2024-12-24 16:30' --public --type night
```
