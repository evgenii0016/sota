"""Фабрика хранилища: memory по умолчанию, PostgreSQL при DATABASE_URL"""

from __future__ import annotations

from app.config import Settings, get_settings
from app.storage.base import TaskRepository
from app.storage.memory import MemoryRepository
from app.storage.migrate import run_migrations
from app.storage.postgres import PostgresRepository

_repository: TaskRepository | None = None


def init_repository(settings: Settings | None = None) -> TaskRepository:
    global _repository
    if _repository is not None:
        return _repository

    settings = settings or get_settings()
    if settings.uses_postgres:
        assert settings.database_url is not None
        run_migrations(settings.database_url)
        repo = PostgresRepository(settings.database_url)
        repo.connect()
        _repository = repo
        return repo

    _repository = MemoryRepository()
    _seed_memory_examples(_repository)
    return _repository


def get_repository() -> TaskRepository:
    return init_repository()


def reset_repository() -> None:
    global _repository
    if _repository is not None and hasattr(_repository, "close"):
        _repository.close()
    _repository = None


def _seed_memory_examples(repo: MemoryRepository) -> None:
    repo.register_example(
        example_id="11111111-1111-4111-8111-111111111101",
        name="Два различных корня",
        statement=(
            "Решите уравнение: x^2 - 5x + 6 = 0. "
            "В ответ запишите все корни через ';' в порядке возрастания."
        ),
        answer="2;3",
        tags=["two_roots"],
    )
    repo.register_example(
        example_id="11111111-1111-4111-8111-111111111102",
        name="Двойной корень",
        statement=(
            "Решите уравнение: x^2 - 4x + 4 = 0. "
            "В ответ запишите все корни через ';' в порядке возрастания."
        ),
        answer="2",
        tags=["double_root"],
    )
    repo.register_example(
        example_id="11111111-1111-4111-8111-111111111103",
        name="Линейное уравнение",
        statement=(
            "Решите уравнение: 2x - 6 = 0. "
            "В ответ запишите все корни через ';' в порядке возрастания."
        ),
        answer="3",
        task_type="linear",
        tags=["linear"],
    )
    repo.register_example(
        example_id="11111111-1111-4111-8111-111111111104",
        name="Рациональное уравнение",
        statement=(
            "Решите уравнение: (x + 16)/(x + 2) = 3. "
            "В ответ запишите все корни через ';' в порядке возрастания."
        ),
        answer="5",
        task_type="rational",
        tags=["rational"],
    )
