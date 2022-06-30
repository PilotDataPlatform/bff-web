# Backend for Frontend

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7](https://img.shields.io/badge/python-3.7-green?style=for-the-badge)](https://www.python.org/)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/pilotdataplatform/bff-web/Run%20Tests/develop?style=for-the-badge)

## About

The BFF is a proxy layer to allow easy access to the pilot microservices from a frontend application. BFF will handling calling the correct APIs to check permissions before calling the microservices.

## Built With
 - [FastAPI](https://fastapi.tiangolo.com/): Async API framework
 - [poetry](https://python-poetry.org/): python package management
 - [docker](https://docker.com)



# Getting Started

## Prerequisites

 1. The project is using poetry to handle the package. **Note here the poetry must install globally not in the anaconda virtual environment**

 ```
 pip install poetry
 ```

 ## Installation

 1. git clone the project:
 ```
 git clone git@github.com:PilotDataPlatform/bff-web.git
 ```

 2. install the package:
 ```
 poetry install
 ```

 3. create the `.env` file from `.env.schema`

 4. run it locally:
 ```
 poetry run python run.py
 ```

## Running with Docker

Add environment variables listed in .env.schema in the docker-compose.yaml file.

Start API with docker-compose:
```
docker-compose build
docker-compose up
```

## Urls
Port can be configured with the environment variable `PORT`
- API: http://localhost:5063
- API docs: http://localhost:5063/v1/api-doc


## API Documents

REST API documentation in the form of Swagger/OpenAPI can be found here: [Api Document](https://pilotdataplatform.github.io/api-docs/)


## Helm Charts

Components of the Pilot Platform are available as helm charts for installation on Kubernetes: [BFF Helm Charts](https://github.com/PilotDataPlatform/helm-charts/tree/main/bff)


# Colaboration

## Run tests

```
poetry run pytest
```

