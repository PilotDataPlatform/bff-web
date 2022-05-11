# Backend for Frontend

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7](https://img.shields.io/badge/python-3.7-green?style=for-the-badge)](https://www.python.org/)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/pilotdataplatform/bff-web/Run%20Tests/develop?style=for-the-badge)

## About

Proxy layer to allow easy access to the pilot microservices from a frontend application.

## Built With
- Python
- Flask


## Running the service

Configure the settings using .env

Start API with docker-compose:
```
docker-compose build
docker-compose up
```

### Urls
Port can be configured with the environment variable `PORT`
- API: http://localhost:5063
- API docs: http://localhost:5063/v1/api-doc

