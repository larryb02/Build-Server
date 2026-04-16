FROM node:22-slim AS frontend

WORKDIR /web
COPY ./web/package*.json ./
RUN npm ci
COPY ./web ./
RUN npm run build

FROM python:3.12.12 AS api

WORKDIR /app
COPY ./buildserver-api /app/
RUN pip install --target /app/dist .

FROM python:3.12.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY --from=api /app/dist /app/dist
COPY --from=frontend /web/dist /dist
ENV PYTHONPATH=/app/dist
ENV PATH=/app/dist/bin:$PATH

ENTRYPOINT ["buildserver", "start"]
