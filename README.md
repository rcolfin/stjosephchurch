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


## Authentication

The YouTube Data API does not support service accounts, so the CLI authenticates as you with an OAuth 2.0
client secret (`credentials.json`) the first time, then reuses the refresh token saved in `token.json`.
The paths can be set with `--credentials` / `--token` or `STJOSEPH_CREDENTIALS` / `STJOSEPH_TOKEN`, and
`--headless` (`STJOSEPH_HEADLESS=1`) fails instead of opening a browser when the token cannot be refreshed.

Both files are stored in Secret Manager (`STJOSEPH_YOUTUBE_CLIENT_SECRET` and `STJOSEPH_YOUTUBE_TOKEN`, created by
[terraform-gcp](https://github.com/rcolfin/terraform-gcp)). [scripts/launch.sh](scripts/launch.sh) downloads them
before running the CLI and uploads the token again whenever you re-authenticate.

> [!IMPORTANT]
> The OAuth consent screen must be published (**Google Auth Platform → Audience → Publish app**). While it is in
> *Testing*, Google expires refresh tokens after 7 days.

## Weekly Scheduling

The `stjoseph-schedule-masses` Cloud Run Job runs every Monday at 6 AM ET and schedules the following week's mass:

```sh
python -m stjoseph schedule-masses --public --days-ahead 7
```

Masses that are already scheduled are skipped, so it can be re-run safely:

```sh
gcloud run jobs execute stjoseph-schedule-masses --region us-central1
```

The image is built by [cloudbuild.yaml](cloudbuild.yaml) on every push to `main`.

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
python -m stjoseph schedule-christmas-pageant $(date '+%Y-12-24 15:55') --schedule-end $(date '+%Y-12-24 16:30') --public
```

To schedule the Christ Pageant mass:

(Schedules the mass on Christmas Eve at 4:30 PM using the Readings for the [Christmas Mass during the Night](https://bible.usccb.org/bible/readings/122526-Night.cfm).)

```sh
python -m stjoseph schedule-mass "$(date '+%Y-12-24 16:30')" --mass-date "$(date '+%Y-12-25')" --schedule-end "$(date '+%Y-12-24 17:30')" --public --type night
```

To schedule the New Year Day mass (Solemnity of Mary, the Holy Mother of God):

```sh
python -m stjoseph schedule-mass "$(date '+%Y-01-01 10:00')" --mass-date "$(date '+%Y-01-01')" --schedule-end "$(date '+%Y-01-01 11:00')" --public
```


To list masses that were scheduled but for whatever reason didn't air or were cut off after a short amount of time (under 15 minutes), then these are eligible for deletion:

```sh
python -m stjoseph list-eligible-for-deletion
```

 To actually remove them:

```sh
python -m stjoseph delete-eligible --no-dry-run
```

To remove scheduled masses for past dates that never went live (prompts before each deletion; use `--force` to skip the prompts or `--dry-run` to only list them):

```sh
python -m stjoseph delete-stale-schedules
```

If a mass went live using the broadcast scheduled for a different date (e.g. the October 17 mass was streamed using the October 10 broadcast), correct the title and description using the readings for the date it actually aired (prompts before each correction; use `--force` to skip the prompts):

```sh
python -m stjoseph correct-mass-dates --dry-run
python -m stjoseph correct-mass-dates
```

To correct a specific broadcast, pass its ID and optionally the date it aired and/or the mass date:

```sh
python -m stjoseph correct-mass-dates <BROADCAST_ID> --date '2026-10-17 17:30'
```

or through the launcher...

```sh
scripts/launch.sh schedule-mass '2026-05-02 17:30' --public
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
scripts/launch.sh schedule-christmas-pageant "$(date '+%Y-12-24 15:55')" --schedule-end "$(date '+%Y-12-24 16:30')" --public
```

To schedule the Christ Pageant mass:

(Schedules the mass on Christmas Eve at 4:30 PM using the Readings for the [Christmas Mass during the Night](https://bible.usccb.org/bible/readings/122526-Night.cfm).)

```sh
scripts/launch.sh schedule-mass "$(date '+%Y-12-24 16:30')" --mass-date "$(date '+%Y-12-25')" --schedule-end "$(date '+%Y-12-24 17:30')" --public --type night
```

To schedule the New Year Day mass (Solemnity of Mary, the Holy Mother of God):

```sh
scripts/launch.sh schedule-mass "$(date '+%Y-01-01 10:00')" --mass-date "$(date '+%Y-01-01')" --schedule-end "$(date '+%Y-01-01 11:00')" --public
```
