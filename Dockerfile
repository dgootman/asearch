# syntax=docker/dockerfile:1

# Based on https://www.docker.com/blog/containerized-python-development-part-1/

FROM python AS python-builder
RUN pip install poetry
COPY pyproject.toml ./
RUN poetry export -f requirements.txt --output requirements.txt

FROM node AS node-builder
WORKDIR /app
COPY package.json tsconfig.json webpack.config.js ./
COPY src/ src/
RUN npm install && npm run build

FROM python:slim
WORKDIR /app
COPY --from=python-builder requirements.txt ./
RUN pip install -r requirements.txt
COPY --from=node-builder /app/dist/ dist/
COPY app.py .
EXPOSE 8000
CMD [ "uvicorn", "app:app", "--host", "0.0.0.0" ]