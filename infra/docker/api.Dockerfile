FROM python:3.12.12 AS builder

WORKDIR /app
COPY ./buildserver-api /app/
RUN pip install --target /app/dist .

FROM python:3.12.12-slim

COPY --from=builder /app/dist /app/dist
COPY .env .env
ENV PYTHONPATH=/app/dist
ENV PATH=/app/dist/bin:$PATH

CMD ["buildserver"]
