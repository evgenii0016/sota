import os

# Тесты всегда офлайн и без PostgreSQL: не подхватываем LLM/БД из локального .env
os.environ.setdefault("LLM_PROVIDER", "fake")
os.environ.pop("DATABASE_URL", None)
