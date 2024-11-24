# syntax=docker/dockerfile:1

# Based on https://www.docker.com/blog/containerized-python-development-part-1/

ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION} AS python-builder
RUN pip install poetry
COPY pyproject.toml ./
RUN poetry export -f requirements.txt --without-hashes --output requirements.txt

FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
COPY --from=python-builder requirements.txt ./
RUN pip install -r requirements.txt
COPY app.py .

EXPOSE 8501

CMD [ "streamlit", "run", "app.py" ]
