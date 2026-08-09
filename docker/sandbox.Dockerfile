FROM python:3.12-slim

RUN useradd -m sandbox
RUN pip install --no-cache-dir pytest

WORKDIR /workspace
USER sandbox
