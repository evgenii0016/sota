# Frontend — задание 13 ЕГЭ

React + TypeScript + Vite. Менеджер пакетов: **pnpm**.

## Страницы

| Маршрут | Назначение |
|---------|------------|
| `/` | Генерация и выбор из 3 вариантов |
| `/solve/:taskId` | Бланк решения |
| `/result/:attemptId` | Оценка и замечания |

## Локальный запуск (без Docker)

```bash
# Терминал 1 — бекенд
cd ..
uvicorn app.main:app --reload --port 8000

# Терминал 2 — фронтенд
cd frontend
pnpm install
pnpm dev
```

Фронтенд: http://localhost:5173
API: http://localhost:8000/docs

В dev-режиме запросы к `/tasks` и `/attempts` проксируются через Vite на бекенд
(см. `VITE_DEV_PROXY_TARGET` в `vite.config.ts`).

## Docker Compose (бек + фронт)

Из корня репозитория:

```bash
docker compose up --build
```

- API: http://localhost:8000
- Фронт: http://localhost:5173

## Production-сборка

```bash
pnpm build
pnpm preview
```

Docker-образ с nginx:

```bash
docker build -t ege-task13-frontend -f Dockerfile .
```

В production nginx проксирует API-маршруты на сервис `app`.

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `VITE_API_URL` | Базовый URL API для сборки. Пусто — относительные пути (прокси/nginx). |
| `VITE_DEV_PROXY_TARGET` | Цель прокси Vite в dev (по умолчанию `http://localhost:8000`). |
| `FRONTEND_PORT` | Порт dev-сервера в docker compose (по умолчанию `5173`). |
| `CORS_ORIGINS` | Origins для CORS бекенда. |
