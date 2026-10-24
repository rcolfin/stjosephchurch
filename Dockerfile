ARG PLATFORM="linux/amd64"

# Debian (not Alpine) so Playwright can install Chromium for the USCCB JavaScript challenge.
FROM --platform=${PLATFORM} ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ARG GIT_COMMIT="unknown"
ARG BUILD_DATE=""
ARG AUTHORS="rcolfin"
ARG APPDIR="/application"

LABEL \
    org.opencontainers.image.revision=$GIT_COMMIT \
    org.opencontainers.image.created=$BUILD_DATE \
    org.opencontainers.image.authors=$AUTHORS \
    org.opencontainers.image.description="St Joseph Mass Scheduler"

ENV \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT="/usr/local" \
    PLAYWRIGHT_BROWSERS_PATH="/ms-playwright"

WORKDIR "${APPDIR}"

# Install the dependencies first so they are cached independently of the source:
COPY pyproject.toml uv.lock README.md ./
RUN \
    uv sync --no-dev --locked --no-install-project --quiet \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY stjoseph ./stjoseph
RUN \
    uv sync --no-dev --locked --no-editable --quiet \
    && rm -rf ./*

RUN useradd --create-home stjoseph
USER stjoseph
WORKDIR /home/stjoseph

# The client secret and token are mounted from Secret Manager (read-only):
ENV \
    STJOSEPH_CREDENTIALS="/secrets/credentials/credentials.json" \
    STJOSEPH_TOKEN="/secrets/token/token.json" \
    STJOSEPH_HEADLESS="1" \
    GIT_COMMIT="${GIT_COMMIT}" \
    BUILD_TIMESTAMP="${BUILD_DATE}"

ENTRYPOINT ["python", "-m", "stjoseph"]

CMD ["--help"]
