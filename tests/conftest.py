import os

# Тесты всегда офлайн: не подхватываем LLM из локального .env
os.environ.setdefault("LLM_PROVIDER", "fake")
