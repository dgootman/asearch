# syntax=docker/dockerfile:1

# Based on https://www.docker.com/blog/containerized-python-development-part-1/

ARG PYTHON_VERSION=3.10

FROM python:${PYTHON_VERSION} AS python-builder
RUN pip install poetry
COPY pyproject.toml ./
RUN poetry export -f requirements.txt --without-hashes --output requirements.txt

FROM node AS node-builder
WORKDIR /app
COPY package.json tsconfig.json webpack.config.js ./
COPY src/ src/
RUN npm install && npm run build

FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
COPY --from=python-builder requirements.txt ./
RUN pip install -r requirements.txt
COPY --from=node-builder /app/dist/ dist/
COPY app.py .
EXPOSE 8000
CMD [ "uvicorn", "app:app", "--host", "0.0.0.0" ]
