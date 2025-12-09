# stjosephchurch

[![CI Build](https://github.com/rcolfin/stjosephchurch/actions/workflows/ci.yml/badge.svg)](https://github.com/stjosephchurch/python/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/rcolfin/stjosephchurch.svg)](https://github.com/rcolfin/stjosephchurch/blob/main/LICENSE)

Package to set up and manage the Live Stream for [Saint Joseph Church Lincoln Park NJ](https://www.youtube.com/@saintjosephchurchlincolnpa905)

To reduce the manual steps involved with setting up a Scheduled Live Stream which includes the [Readings](https://bible.usccb.org/bible/readings/), I came up with this app to sources the Readings from [catholic-mass-readings](https://github.com/rcolfin/catholic-mass-readings) package, then utilizing the [YouTube Data API v3](https://developers.google.com/youtube/v3) to insert (or update) the masses on the YouTube Channel.  Through the CLI below, I can schedule the masses for the entire year (only what is available via the [Readings](https://bible.usccb.org/bible/readings/) website) within a matter of seconds.


## Development

### Setup Python Environment:

Run [scripts/console.sh](../scripts/console.sh)

### If you need to relock:

Run [scripts/lock.sh](../scripts/lock.sh)

### Run code

Run [scripts/console.sh](../scripts/console.sh) uv run python -m stjoseph


## API Usage:

As a CLI

To schedule a mass:

```sh
python -m stjoseph schedule-mass '2026-01-03 17:30' --public
```

To schedule Sunday masses a month in advance:

```sh
python -m stjoseph schedule-masses --public --end $(date -d "+1 month" +%Y-%m-%d)
```

To schedule all Sunday masses up to a year:

```sh
python -m stjoseph schedule-masses --public
```

To schedule the Christ Pageant:

(Schedules the Christmas Pageant at 4:00 PM.)

```sh
python -m stjoseph schedule-christmas-pageant $(date '+%Y-12-24 16:00') --schedule-end $(date '+%Y-12-24 16:30') --public
```

To schedule the Christ Pageant mass:

(Schedules the mass on Christmas Eve at 4:30 PM using the Readings for the [Christmas Mass during the Night](https://bible.usccb.org/bible/readings/122524-Night.cfm).)

```sh
python -m stjoseph schedule-mass "$(date '+%Y-12-24 16:30')" --mass-date "$(date '+%Y-12-25')" --schedule-end "$(date '+%Y-12-24 17:30')" --public --type night
```

To list masses that were scheduled but for whatever reason didn't air or were cut off after a short amount of time (under 15 minutes), then these are eligible for deletion:

```sh
python -m stjoseph list-eligible-for-deletion
```

 To actually remove them:

```sh
python -m stjoseph delete-eligible --no-dry-run
```

or through the launcher...

```sh
scripts/launch.sh schedule-mass '2026-12-21 17:30' --public
```

To schedule Sunday masses a month in advance:

```sh
scripts/launch.sh schedule-masses --public --end "$(date -d '+1 month' +%Y-%m-%d)"
```

To schedule all Sunday masses up to a year:

```sh
scripts/launch.sh schedule-masses --public
```

To schedule the Christ Pageant:

(Schedules the Christmas Pageant at 4:00 PM.)

```sh
scripts/launch.sh schedule-christmas-pageant "$(date -d "+1 month" '+%Y-12-24 16:00')" --schedule-end "$(date -d '+1 month' +%Y-12-24 16:30)" --public
```

To schedule the Christ Pageant mass:

(Schedules the mass on Christmas Eve at 4:30 PM using the Readings for the [Christmas Vigil Mass](https://bible.usccb.org/bible/readings/122524-vigil.cfm).)

```sh
scripts/launch.sh schedule-mass "$(date '+%Y-12-24 16:30')" --mass-date "$(date '+%Y-12-25')" --schedule-end "$(date '+%Y-12-24 17:30')" --public --type vigil
```
