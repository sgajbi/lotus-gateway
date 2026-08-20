FROM python:3.11-slim AS base

ARG LOTUS_APP_VERSION=0.1.0
ARG LOTUS_GIT_COMMIT_SHA=unknown
ARG LOTUS_GIT_BRANCH=unknown
ARG LOTUS_BUILD_TIMESTAMP=unknown
ARG LOTUS_REPO_URL=unknown
ARG LOTUS_CI_RUN_ID=unknown

LABEL org.opencontainers.image.title="lotus-gateway" \
      org.opencontainers.image.description="Lotus Gateway experience API" \
      org.opencontainers.image.version="${LOTUS_APP_VERSION}" \
      org.opencontainers.image.revision="${LOTUS_GIT_COMMIT_SHA}" \
      org.opencontainers.image.ref.name="${LOTUS_GIT_BRANCH}" \
      org.opencontainers.image.created="${LOTUS_BUILD_TIMESTAMP}" \
      org.opencontainers.image.source="${LOTUS_REPO_URL}" \
      com.lotus.ci.run-id="${LOTUS_CI_RUN_ID}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOTUS_APP_VERSION="${LOTUS_APP_VERSION}" \
    LOTUS_GIT_COMMIT_SHA="${LOTUS_GIT_COMMIT_SHA}" \
    LOTUS_GIT_BRANCH="${LOTUS_GIT_BRANCH}" \
    LOTUS_BUILD_TIMESTAMP="${LOTUS_BUILD_TIMESTAMP}" \
    LOTUS_REPO_URL="${LOTUS_REPO_URL}" \
    LOTUS_CI_RUN_ID="${LOTUS_CI_RUN_ID}"

WORKDIR /app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade --yes --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir . \
    && pip uninstall --yes wheel jaraco.context setuptools \
    && pip cache purge

EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100", "--app-dir", "src"]
