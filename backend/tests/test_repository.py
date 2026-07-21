from backend.anvaya.repositories.base import Repository
from backend.anvaya.repositories.sqlite import SQLiteRepository


def test_sqlite_repository_implements_contract():
    repository = SQLiteRepository.from_url("sqlite:///:memory:")
    assert isinstance(repository, Repository)
    assert repository.health_check() == "ok"
    repository.close()


def test_sqlite_repository_rejects_non_sqlite_url():
    try:
        SQLiteRepository.from_url("postgresql://not-supported")
    except ValueError as error:
        assert "sqlite:///" in str(error)
    else:
        raise AssertionError("Expected unsupported repository URL to fail")
