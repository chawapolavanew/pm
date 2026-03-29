#!/usr/bin/env bash
set -e
docker stop kanban-pm 2>/dev/null || true
docker rm kanban-pm 2>/dev/null || true
echo "Stopped"
