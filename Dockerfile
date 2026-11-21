# ---- build stage ----
FROM python:3.12-slim AS build
WORKDIR /w
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage: small, non-root ----
FROM python:3.12-slim
ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA} PYTHONUNBUFFERED=1
# Pull in OS security patches released since the base image was built
# (e.g. the zlib1g fix Trivy flagged), then drop the apt cache to keep the image small.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /install /usr/local
WORKDIR /srv
COPY app ./app
RUN useradd -r -u 10001 appuser
USER 10001
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8080/healthz')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
