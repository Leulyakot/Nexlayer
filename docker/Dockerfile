FROM python:3.11-slim AS base

WORKDIR /app

RUN groupadd -r nexlayer && useradd -r -g nexlayer nexlayer

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY nexlayer/ ./nexlayer/
COPY config/ ./config/

RUN chown -R nexlayer:nexlayer /app

USER nexlayer

EXPOSE 8000

CMD ["uvicorn", "nexlayer.main:app", "--host", "0.0.0.0", "--port", "8000"]
