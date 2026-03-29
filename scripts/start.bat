@echo off
cd /d "%~dp0.."

docker build -t kanban-pm .
docker run -d ^
  --name kanban-pm ^
  --env-file .env ^
  -p 8000:8000 ^
  -v "%cd%/data:/app/data" ^
  kanban-pm

echo Running at http://localhost:8000
