FROM python:3.13.9-alpine3.22 AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIPENV_NOSPIN=1

RUN apk add --no-cache build-base python3-dev postgresql-dev

WORKDIR /build

COPY applications/statistics_api/Pipfile* /build/

RUN pip install --no-cache-dir pipenv

RUN if [ -f Pipfile.lock ]; then \
      if pipenv lock --help | grep -q -- '--requirements'; then \
        pipenv lock --requirements > requirements.txt; \
      else \
        pipenv requirements > requirements.txt; \
      fi; \
    else \
      pipenv lock --clear; \
      if pipenv lock --help | grep -q -- '--requirements'; then \
        pipenv lock --requirements > requirements.txt; \
      else \
        pipenv requirements > requirements.txt; \
      fi; \
    fi

RUN pip wheel --no-cache-dir -r requirements.txt -w /wheels


FROM python:3.13.9-alpine3.22 AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache postgresql-libs

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt

COPY applications/common ./common
COPY applications/statistics_api ./statistics_api

RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001

EXPOSE 8000
CMD ["gunicorn", "statistics_api.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4"]
