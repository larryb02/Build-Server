FROM python:3.12.12 AS builder

WORKDIR /app
COPY ./buildserver-runner /app/
RUN pip install --target /app/dist .

FROM python:3.12.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist /app/dist
ENV PYTHONPATH=/app/dist
ENV PATH=/app/dist/bin:$PATH

CMD ["buildserver-runner", "start"]
