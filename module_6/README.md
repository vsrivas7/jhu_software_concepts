# Module 6 — GradCafe Microservice Application

## Overview
A containerized microservice refactor of the GradCafe Flask app using Docker Compose, RabbitMQ, and PostgreSQL.

## Architecture
- **web** — Flask app on port 8080, publishes tasks to RabbitMQ
- **worker** — Python consumer, processes tasks and writes to PostgreSQL
- **db** — PostgreSQL database
- **rabbitmq** — Message broker (management UI on port 15672)

## Running the App

### Prerequisites
- Docker Desktop installed and running

### Start all services
```bash
docker compose up --build
```

### Access
- App: http://localhost:8080/analysis
- RabbitMQ UI: http://localhost:15672 (guest / guest)

### Stop
```bash
docker compose down
```

## Docker Hub Images
- Web: https://hub.docker.com/r/vshfrm/module_6
- Worker: https://hub.docker.com/r/vshfrm/module_6-worker

Pull and run directly:
```bash
docker pull vshfrm/module_6:v1
docker pull vshfrm/module_6-worker:v1
```

## Running Tests
```bash
pip install -r requirements.txt
python -m pytest tests/test_app.py --cov=src/web --cov=src/worker
```

## Lint
```bash
pylint src/web/run.py src/web/publisher.py src/web/app/query_data.py src/web/app/db.py src/worker/consumer.py
```

## Ports
| Service   | Port  |
|-----------|-------|
| Flask app | 8080  |
| RabbitMQ  | 15672 |
| PostgreSQL| 5432  |
