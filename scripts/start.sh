#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

docker build -t kanban-pm .
docker run -d \
  --name kanban-pm \
  --env-file .env \
  -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  kanban-pm

echo "Running at http://localhost:8000"
